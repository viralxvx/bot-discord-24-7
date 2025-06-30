import discord
import re
import datetime
from discord_bot import bot
from config import CANAL_REPORTES, CANAL_SOPORTE, CANAL_OBJETIVO, CANAL_NORMAS_GENERALES, CANAL_X_NORMAS, CANAL_ANUNCIOS, CANAL_FALTAS, MAX_MENSAJES_RECIENTES, MENSAJE_NORMAS
from state_management import ultima_publicacion_dict, amonestaciones, faltas_dict, save_state, active_conversations, mensajes_recientes
from utils import actualizar_mensaje_faltas, registrar_log, publicar_mensaje_unico
from views import ReportMenu, SupportMenu

@bot.event
async def on_message(message):
    from config import CANAL_LOGS
    
    if message.channel.name not in [CANAL_LOGS, CANAL_FALTAS]:
        canal_id = str(message.channel.id)
        mensaje_normalizado = message.content.strip().lower()
        if mensaje_normalizado:
            if any(mensaje_normalizado == msg.strip().lower() for msg in mensajes_recientes[canal_id]):
                try:
                    await message.delete()
                    if message.author != bot.user:
                        try:
                            await message.author.send(
                                f"⚠️ **Mensaje repetido eliminado** en #{message.channel.name}"
                            )
                        except:
                            pass
                except discord.Forbidden:
                    pass
            mensajes_recientes[canal_id].append(message.content)
            if len(mensajes_recientes[canal_id]) > MAX_MENSAJES_RECIENTES:
                mensajes_recientes[canal_id].pop(0)
            await save_state()
    
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        if message.mentions:
            reportado = message.mentions[0]
            await message.channel.send(
                f"📃 **Reportando a {reportado.mention}**",
                view=ReportMenu(reportado, message.author)
            )
            await message.delete()
        else:
            await message.channel.send("⚠️ **Menciona un usuario** o usa `!permiso <días>`")
            
    elif message.channel.name == CANAL_SOPORTE and not message.author.bot:
        user_id = message.author.id
        if user_id not in active_conversations:
            active_conversations[user_id] = {"message_ids": [], "last_time": datetime.datetime.now(datetime.timezone.utc)}
            
        if message.content.lower() in ["salir", "cancelar", "fin", "ver reglas"]:
            if message.content.lower() == "ver reglas":
                msg = await message.channel.send(MENSAJE_NORMAS)
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
                faltas_dict[user_id]["aciertos"] += 1
                if canal_faltas:
                    await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[user_id]["faltas"], faltas_dict[user_id]["aciertos"], faltas_dict[user_id]["estado"])
            else:
                msg = await message.channel.send("✅ **Consulta cerrada**")
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
            await message.delete()
            return
            
        msg = await message.channel.send("👋 **Selecciona una opción**", view=SupportMenu(message.author, message.content))
        active_conversations[user_id]["message_ids"].append(msg.id)
        active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
        await message.delete()
        
    elif message.channel.name == CANAL_OBJETIVO and not message.author.bot:
        ahora = datetime.datetime.now(datetime.timezone.utc)
        urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
        
        if len(urls) != 1 or (len(urls) == 1 and message.content.strip() != urls[0]):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(f"{message.author.mention} **Formato incorrecto**")
            await advertencia.delete(delay=15)
            try:
                await message.author.send(f"⚠️ **Falta**: Formato incorrecto en #🧵go-viral")
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
            
        url = urls[0].split('?')[0]
        url_pattern = r"https://x\.com/[^/]+/status/\d+"
        if not re.match(url_pattern, url):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(f"{message.author.mention} **URL inválida**")
            await advertencia.delete(delay=15)
            try:
                await message.author.send(f"⚠️ **Falta**: URL inválida en #🧵go-viral")
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
            
        new_message = message
        mensajes = []
        async for msg in message.channel.history(limit=100):
            if msg.id == new_message.id or msg.author == bot.user:
                continue
            mensajes.append(msg)
            
        ultima_publicacion = None
        for msg in mensajes:
            if msg.author == message.author:
                ultima_publicacion = msg
                break
                
        if not ultima_publicacion:
            ultima_publicacion_dict[message.author.id] = ahora
            faltas_dict[message.author.id]["aciertos"] += 1
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
            
        diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
        publicaciones_despues = [m for m in mensajes if m.created_at > ultima_publicacion.created_at and m.author != message.author]
        
        no_apoyados = []
        for msg in publicaciones_despues:
            apoyo = False
            for reaction in msg.reactions:
                if str(reaction.emoji) == "🔥":
                    async for user in reaction.users():
                        if user == message.author:
                            apoyo = True
                            break
            if not apoyo:
                no_apoyados.append(msg)
                
        if no_apoyados:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(f"{message.author.mention} **Falta de reacciones**")
            await advertencia.delete(delay=15)
            try:
                await message.author.send(f"⚠️ **Falta**: Reacciones pendientes en #🧵go-viral")
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
            
        if len(publicaciones_despues) < 1 and diferencia.total_seconds() < 86400:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(f"{message.author.mention} **Espera 24h**")
            await advertencia.delete(delay=15)
            try:
                await message.author.send(f"⚠️ **Falta**: Publicación antes de 24h")
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
            
        def check_reaccion_propia(reaction, user):
            return reaction.message.id == new_message.id and str(reaction.emoji) == "👍" and user == message.author
            
        try:
            await bot.wait_for("reaction_add", timeout=60, check=check_reaccion_propia)
            faltas_dict[message.author.id]["aciertos"] += 1
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
        except:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(f"{message.author.mention} **Falta reacción propia**")
            await advertencia.delete(delay=15)
            try:
                await message.author.send(f"⚠️ **Falta**: Sin reacción 👍 propia")
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
            
        ultima_publicacion_dict[message.author.id] = ahora
        await save_state()
        
    elif message.channel.name in [CANAL_NORMAS_GENERALES, CANAL_X_NORMAS] and not message.author.bot:
        canal_anuncios = discord.utils.get(message.guild.text_channels, name=CANAL_ANUNCIOS)
        if canal_anuncios:
            await publicar_mensaje_unico(canal_anuncios, f"📢 **Norma actualizada**: {message.channel.mention}")
            
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.message.channel.name != CANAL_OBJETIVO:
        return
        
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    autor = reaction.message.author
    emoji_valido = "👍" if user == autor else "🔥"
    ahora = datetime.datetime.now(datetime.timezone.utc)
    
    if str(reaction.emoji) != emoji_valido:
        await reaction.remove(user)
        faltas_dict[user.id]["faltas"] += 1
        faltas_dict[user.id]["ultima_falta_time"] = ahora
        advertencia = await reaction.message.channel.send(f"{user.mention} **Emoji incorrecto**")
        await advertencia.delete(delay=15)
        try:
            await user.send(f"⚠️ **Falta**: Reacción incorrecta en #🧵go-viral")
        except:
            pass
        if canal_faltas:
            await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], faltas_dict[user.id]["estado"])
            
    elif str(reaction.emoji) == "🔥" and user == autor:
        await reaction.remove(user)
        faltas_dict[user.id]["faltas"] += 1
        faltas_dict[user.id]["ultima_falta_time"] = ahora
        advertencia = await reaction.message.channel.send(f"{user.mention} **No uses 🔥 en tu post**")
        await advertencia.delete(delay=15)
        try:
            await user.send(f"⚠️ **Falta**: 🔥 en tu propia publicación")
        except:
            pass
        if canal_faltas:
            await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], faltas_dict[user.id]["estado"])
            
    await save_state()
