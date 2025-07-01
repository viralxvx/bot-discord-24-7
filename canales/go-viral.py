# canales/go-viral.py

import discord
import re
import asyncio
from discord.ext import commands
from discord_bot import bot
from config import CANAL_OBJETIVO, CANAL_FALTAS
from state_management import ultima_publicacion_dict, faltas_dict, save_state
from canales.logs import registrar_log
from utils import actualizar_mensaje_faltas

URL_REGEX = re.compile(r"https://x\.com/\w+/status/(\d+)")
URL_CORRECCION_REGEX = re.compile(r"(https://x\.com/\w+/status/\d+)(\?.*)?")

@bot.event
async def on_message(message):
    if message.channel.name != CANAL_OBJETIVO or message.author.bot:
        return

    autor = message.author
    contenido = message.content.strip()
    urls = re.findall(URL_REGEX, contenido)
    canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)

    # Solo se permite una URL válida y sin texto adicional
    if not URL_REGEX.fullmatch(contenido):
        # Intentar corregir el formato del link automáticamente
        corregido = re.sub(URL_CORRECCION_REGEX, r"\1", contenido)
        if URL_REGEX.fullmatch(corregido):
            await message.delete()
            nuevo_mensaje = await message.channel.send(corregido)
            await nuevo_mensaje.add_reaction("👍")
            await registrar_log(f"🔧 Link corregido automáticamente para {autor.name}", categoria="go-viral")
            await notificar_temp(message.channel, autor, "🔧 Tu enlace fue corregido automáticamente. Por favor usa el formato limpio en el futuro.")
            try:
                await autor.send("🧼 Tu enlace fue corregido automáticamente por el bot. Asegúrate de usar el formato limpio: `https://x.com/usuario/status/ID`.")
            except:
                pass
            return
        else:
            await sancionar(autor, message, "El mensaje no contiene una URL válida de X.", canal_faltas)
            return

    # Verifica que hayan al menos 2 publicaciones de otros desde su último post
    historial = [msg async for msg in message.channel.history(limit=50)]
    publicaciones_despues = [
        m for m in historial
        if m.author != autor and URL_REGEX.fullmatch(m.content)
        and m.created_at > ultima_publicacion_dict.get(autor.id, message.created_at)
    ]

    if len(publicaciones_despues) < 2:
        await sancionar(autor, message, "Debes esperar al menos 2 publicaciones de otros usuarios antes de volver a publicar.", canal_faltas)
        return

    # Registra última publicación válida
    ultima_publicacion_dict[autor.id] = message.created_at
    faltas_dict.setdefault(autor.id, {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None})
    faltas_dict[autor.id]["aciertos"] += 1
    await actualizar_mensaje_faltas(canal_faltas, autor, faltas_dict[autor.id]["faltas"], faltas_dict[autor.id]["aciertos"], "OK")
    await registrar_log(f"✅ Publicación válida de {autor.name}", categoria="go-viral")
    save_state()

async def sancionar(usuario, mensaje, motivo, canal_faltas):
    await mensaje.delete()
    faltas_dict.setdefault(usuario.id, {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None})
    faltas_dict[usuario.id]["faltas"] += 1
    await actualizar_mensaje_faltas(canal_faltas, usuario, faltas_dict[usuario.id]["faltas"], faltas_dict[usuario.id]["aciertos"], "OK")
    await registrar_log(f"⚠️ Falta por {usuario.name}: {motivo}", categoria="go-viral")

    # Mensaje temporal en el canal
    await notificar_temp(mensaje.channel, usuario, f"⚠️ {motivo}")

    # Mensaje privado
    try:
        await usuario.send(f"⚠️ Tu mensaje fue eliminado por: {motivo}\nCorrígelo para evitar más sanciones en #🧵go-viral.")
    except:
        pass

    save_state()

async def notificar_temp(canal, usuario, texto, duracion=15):
    aviso = await canal.send(f"{usuario.mention} {texto}")
    await asyncio.sleep(duracion)
    await aviso.delete()
