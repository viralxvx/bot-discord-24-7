import discord
import datetime
import re
from discord.ext import commands
from views.report_menu import ReportMenu
from views.support_menu import SupportMenu
from handlers.faltas import actualizar_mensaje_faltas
from handlers.go_viral import faltas_dict, amonestaciones, ultima_publicacion_dict, baneos_temporales
from utils import registrar_log, save_state
from config import CANAL_LOGS, CANAL_FALTAS, CANAL_REPORTES, CANAL_SOPORTE, CANAL_OBJETIVO, CANAL_NORMAS_GENERALES, CANAL_ANUNCIOS, CANAL_X_NORMAS, MAX_MENSAJES_RECIENTES

mensajes_recientes = {}  # {canal_id: [mensajes]}
active_conversations = {}  # {user_id: {"message_ids": [], "last_time": datetime}}

async def on_message(message):
    global active_conversations, mensajes_recientes
    if message.channel.name not in [CANAL_LOGS, CANAL_FALTAS]:
        canal_id = str(message.channel.id)
        mensaje_normalizado = message.content.strip().lower()
        if mensaje_normalizado:
            if canal_id not in mensajes_recientes:
                mensajes_recientes[canal_id] = []
            if any(mensaje_normalizado == msg.strip().lower() for msg in mensajes_recientes[canal_id]):
                try:
                    await message.delete()
                    if message.author != message.guild.me:
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
            save_state()

    canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)

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
                msg = await message.channel.send("**Normas de la comunidad:**\n" + "Aquí va el mensaje de normas...")  # Puedes cambiar por mensaje real o llamar handler
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
                if user_id in faltas_dict:
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
            if msg.id == new_message.id or msg.author == message.guild.me:
                continue
            mensajes.append(msg)

        ultima_publicacion = None
        for msg in mensajes:
            if msg.author == message.author:
                ultima_publicacion = msg
                break

        if not ultima_publicacion:
            ultima_publicacion_dict[message.author.id] = ahora
            if message.author.id in faltas_dict:
                faltas_dict[message.author.id]["aciertos"] += 1
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return

        diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
        publicaciones_despues = [m for m in mensajes if m.created_at > ultima_publicacion.created_at and m.author != message.author]
        no_apoyados = []

        for msg in mensajes:
            if msg.created_at > ultima_publicacion.created_at and msg.author != message.author:
                apoyo = False
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "🔥":
                        async for user in reaction.users():
                            if user == message.author:
                                apoyo = True
                                if user.id in faltas_dict:
                                    faltas_dict[user.id]["aciertos"] += 1
                                if canal_faltas:
                                    await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], faltas_dict[user.id]["estado"])
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
            await message.guild.bot.wait_for("reaction_add", timeout=60, check=check_reaccion_propia)
            if message.author.id in faltas_dict:
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

    elif message.channel.name in [CANAL_NORMAS_GENERALES, CANAL_X_NORMAS] and not message.author.bot:
        canal_anuncios = discord.utils.get(message.guild.text_channels, name=CANAL_ANUNCIOS)
        if canal_anuncios:
            await canal_anuncios.send(f"📢 **Norma actualizada**: {message.channel.mention}")

    await message.guild.bot.process_commands(message)
