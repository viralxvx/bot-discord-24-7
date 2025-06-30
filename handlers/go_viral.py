import re
import discord
import datetime
from discord_bot import bot
from state_management import ultima_publicacion_dict, faltas_dict, save_state
from utils import actualizar_mensaje_faltas, registrar_log
from config import CANAL_OBJETIVO, CANAL_FALTAS

async def handle_go_viral_message(message):
    if message.channel.name != CANAL_OBJETIVO or message.author.bot:
        return
        
    ahora = datetime.datetime.now(datetime.timezone.utc)
    urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
    
    # Validación de formato
    if len(urls) != 1 or (len(urls) == 1 and message.content.strip() != urls[0]):
        await handle_invalid_format(message, ahora)
        return
        
    url = urls[0].split('?')[0]
    url_pattern = r"https://x\.com/[^/]+/status/\d+"
    if not re.match(url_pattern, url):
        await handle_invalid_format(message, ahora)
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
        canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)
        if canal_faltas:
            await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
        return
        
    diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=datetime.timezone.utc)
    publicaciones_despues = [m for m in mensajes if m.created_at.replace(tzinfo=datetime.timezone.utc) > ultima_publicacion.created_at.replace(tzinfo=datetime.timezone.utc) and m.author != message.author]
    
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
        await handle_missing_reactions(message, ahora, no_apoyados)
        return
        
    if len(publicaciones_despues) < 1 and diferencia.total_seconds() < 86400:
        await handle_early_post(message, ahora)
        return
        
    # Esperar reacción propia
    def check_reaccion_propia(reaction, user):
        return reaction.message.id == new_message.id and str(reaction.emoji) == "👍" and user == message.author
        
    try:
        await bot.wait_for("reaction_add", timeout=60, check=check_reaccion_propia)
        faltas_dict[message.author.id]["aciertos"] += 1
        canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)
        if canal_faltas:
            await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
    except:
        await handle_missing_self_reaction(message, ahora)
        return
        
    ultima_publicacion_dict[message.author.id] = ahora
    save_state()

async def handle_invalid_format(message, ahora):
    await message.delete()
    faltas_dict[message.author.id]["faltas"] += 1
    faltas_dict[message.author.id]["ultima_falta_time"] = ahora
    advertencia = await message.channel.send(f"{message.author.mention} **Formato incorrecto**")
    await advertencia.delete(delay=15)
    try:
        await message.author.send(f"⚠️ **Falta**: Formato incorrecto en #🧵go-viral")
    except:
        pass
    canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)
    if canal_faltas:
        await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])

async def handle_missing_reactions(message, ahora, no_apoyados):
    await message.delete()
    faltas_dict[message.author.id]["faltas"] += 1
    faltas_dict[message.author.id]["ultima_falta_time"] = ahora
    advertencia = await message.channel.send(f"{message.author.mention} **Falta de reacciones**")
    await advertencia.delete(delay=15)
    try:
        await message.author.send(f"⚠️ **Falta**: Reacciones pendientes en #🧵go-viral")
    except:
        pass
    canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)
    if canal_faltas:
        await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])

async def handle_early_post(message, ahora):
    await message.delete()
    faltas_dict[message.author.id]["faltas"] += 1
    faltas_dict[message.author.id]["ultima_falta_time"] = ahora
    advertencia = await message.channel.send(f"{message.author.mention} **Espera 24h**")
    await advertencia.delete(delay=15)
    try:
        await message.author.send(f"⚠️ **Falta**: Publicación antes de 24h")
    except:
        pass
    canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)
    if canal_faltas:
        await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])

async def handle_missing_self_reaction(message, ahora):
    await message.delete()
    faltas_dict[message.author.id]["faltas"] += 1
    faltas_dict[message.author.id]["ultima_falta_time"] = ahora
    advertencia = await message.channel.send(f"{message.author.mention} **Falta reacción propia**")
    await advertencia.delete(delay=15)
    try:
        await message.author.send(f"⚠️ **Falta**: Sin reacción 👍 propia")
    except:
        pass
    canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)
    if canal_faltas:
        await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
