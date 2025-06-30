import re
import discord
import datetime
from redis_database import get_redis_instance
from handlers.faltas import actualizar_mensaje_faltas
from handlers.logs import registrar_log

redis = get_redis_instance()

CANAL_FALTAS = "📤faltas"
EMOJI_REACCION = "🔥"
EMOJI_PROPIO = "👍"

URL_REGEX = r"https://x\.com/[^/]+/status/\d+"

async def manejar_go_viral(message: discord.Message):
    ahora = datetime.datetime.now(datetime.timezone.utc)
    user_id = str(message.author.id)
    canal_faltas = discord.utils.get(message.guild.text_channels, name=CANAL_FALTAS)

    # Validación del formato de URL
    urls = re.findall(URL_REGEX, message.content)
    if len(urls) != 1:
        await message.delete()
        await enviar_advertencia(message, "Formato incorrecto", "⚠️ Formato inválido. Asegúrate de pegar solo una URL válida de X.")
        await registrar_falta(message.author, canal_faltas, motivo="Formato incorrecto")
        return

    url = urls[0].split('?')[0]

    # Verificar última publicación del autor
    historial = [msg async for msg in message.channel.history(limit=100) if msg.author == message.author and msg.id != message.id]
    if historial:
        ultima_publicacion = historial[0]
        tiempo_diff = ahora - ultima_publicacion.created_at.replace(tzinfo=datetime.timezone.utc)
        if tiempo_diff.total_seconds() < 86400:
            await message.delete()
            await enviar_advertencia(message, "Debes esperar 24h", "⏱️ Aún no han pasado 24 horas desde tu último post.")
            await registrar_falta(message.author, canal_faltas, motivo="Publicación antes de 24h")
            return

    # Verificar reacciones a otros posts
    mensajes = [msg async for msg in message.channel.history(limit=100) if msg.author != message.author and not msg.author.bot]
    no_reaccionados = []

    for msg in mensajes:
        reaccion_valida = False
        for reaction in msg.reactions:
            if str(reaction.emoji) == EMOJI_REACCION:
                async for user in reaction.users():
                    if user.id == message.author.id:
                        reaccion_valida = True
                        break
        if not reaccion_valida:
            no_reaccionados.append(msg)

    if no_reaccionados:
        await message.delete()
        await enviar_advertencia(message, "Reacciones pendientes", "🔥 Debes reaccionar a las publicaciones anteriores antes de enviar la tuya.")
        await registrar_falta(message.author, canal_faltas, motivo="No reaccionó a publicaciones previas")
        return

    # Esperar reacción propia 👍
    def check(reaction, user):
        return reaction.message.id == message.id and str(reaction.emoji) == EMOJI_PROPIO and user == message.author

    try:
        await message.add_reaction("👍")
        await message.client.wait_for("reaction_add", timeout=60, check=check)
    except:
        await message.delete()
        await enviar_advertencia(message, "Falta reacción propia", "👍 Debes reaccionar a tu propia publicación.")
        await registrar_falta(message.author, canal_faltas, motivo="Sin reacción propia")
        return

    # Registrar acierto si todo salió bien
    redis.hincrby(f"faltas:{user_id}", "aciertos", 1)
    await actualizar_mensaje_faltas(canal_faltas, message.author,
        faltas=int(redis.hget(f"faltas:{user_id}", "faltas") or 0),
        aciertos=int(redis.hget(f"faltas:{user_id}", "aciertos") or 1),
        estado=redis.hget(f"faltas:{user_id}", "estado") or "Activo"
    )
    await registrar_log(f"✅ Publicación correcta por {message.author.name}", categoria="go_viral")

async def enviar_advertencia(message, titulo, detalle):
    advertencia = await message.channel.send(f"{message.author.mention} **{titulo}**\n{detalle}")
    await advertencia.delete(delay=15)
    try:
        await message.author.send(f"⚠️ {detalle}")
    except:
        pass

async def registrar_falta(usuario, canal_faltas, motivo):
    user_id = str(usuario.id)
    redis.hincrby(f"faltas:{user_id}", "faltas", 1)
    redis.hset(f"faltas:{user_id}", "ultima_falta_time", datetime.datetime.utcnow().isoformat())
    await actualizar_mensaje_faltas(canal_faltas, usuario,
        faltas=int(redis.hget(f"faltas:{user_id}", "faltas") or 1),
        aciertos=int(redis.hget(f"faltas:{user_id}", "aciertos") or 0),
        estado=redis.hget(f"faltas:{user_id}", "estado") or "Activo"
    )
    await registrar_log(f"❌ Falta de {usuario.name}: {motivo}", categoria="go_viral")
