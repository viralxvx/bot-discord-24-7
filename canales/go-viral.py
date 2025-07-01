import re
import discord
from discord.ext import commands
from discord_bot import bot
from config import CANAL_OBJETIVO, CANAL_FALTAS
from state_management import ultima_publicacion_dict, faltas_dict, save_state
from utils import registrar_log

URL_REGEX = r"https:\/\/x\.com\/[\w\d_]+\/status\/(\d+)"
URL_CORRECCION_REGEX = r"(https:\/\/x\.com\/[\w\d_]+\/status\/\d+)"

# Corrección automática de enlaces
def corregir_url(contenido):
    match = re.search(URL_CORRECCION_REGEX, contenido)
    return match.group(1) if match else None

@bot.event
async def on_message(message):
    if message.channel.name != CANAL_OBJETIVO or message.author.bot:
        return

    autor = message.author
    contenido = message.content.strip()
    canal = message.channel

    # Corregir el formato del link si es necesario
    url_corregida = corregir_url(contenido)

    if not url_corregida:
        await mensaje_temporal(canal, autor, "❌ El enlace no tiene el formato correcto. Usa `https://x.com/usuario/status/ID`.")
        await aplicar_falta(autor, motivo="Enlace inválido")
        await message.delete()
        return

    if url_corregida != contenido:
        try:
            await message.delete()
            nuevo_mensaje = await canal.send(url_corregida)
            await registrar_log(f"{autor.name} publicó URL corregida automáticamente.")
            await mensaje_temporal(canal, autor, f"✏️ Tu link fue corregido automáticamente.\nFormato correcto: `{url_corregida}`", segundos=15)
        except Exception:
            await registrar_log(f"Error al corregir y reenviar mensaje de {autor.name}")
        return

    # Reglas: verificar si puede publicar
    historial = await canal.history(limit=50).flatten()
    publicaciones_anteriores = [
        msg for msg in historial
        if msg.author != autor and not msg.author.bot and re.search(URL_REGEX, msg.content)
    ]
    
    if autor.id in ultima_publicacion_dict:
        ult_idx = next((i for i, msg in enumerate(historial) if msg.author == autor), None)
        if ult_idx is not None:
            posteriores = publicaciones_anteriores[:ult_idx]
            if len(posteriores) < 2:
                await mensaje_temporal(canal, autor, "⛔ Debes esperar al menos 2 publicaciones válidas de otros usuarios antes de volver a publicar.")
                await aplicar_falta(autor, motivo="Publicó sin esperar 2 posts de otros")
                await message.delete()
                return

    # Registrar última publicación
    ultima_publicacion_dict[autor.id] = message.created_at
    save_state()

async def mensaje_temporal(canal, usuario, contenido, segundos=15):
    try:
        mensaje = await canal.send(f"{usuario.mention} {contenido}")
        await usuario.send(f"⚠️ {contenido}")
        await registrar_log(f"Notificación a {usuario.name}: {contenido}")
        await mensaje.delete(delay=segundos)
    except:
        pass

async def aplicar_falta(usuario, motivo="Falta"):
    if usuario.id not in faltas_dict:
        faltas_dict[usuario.id] = {"faltas": 0, "estado": "OK", "aciertos": 0, "mensaje_id": None}
    faltas_dict[usuario.id]["faltas"] += 1
    save_state()
    await registrar_log(f"❌ Falta aplicada a {usuario.name}: {motivo}", categoria="faltas")
