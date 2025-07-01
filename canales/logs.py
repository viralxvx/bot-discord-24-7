# canales/logs.py

import datetime
import discord
from config import CANAL_LOGS, MAX_LOG_LENGTH

async def registrar_log(bot, texto: str, categoria: str = "general"):
    """Registra una entrada en el canal de logs con categoría y timestamp."""
    canal_log = bot.get_channel(CANAL_LOGS)
    if not canal_log or not texto:
        return

    try:
        if len(texto) > MAX_LOG_LENGTH:
            texto = texto[:MAX_LOG_LENGTH] + "..."

        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{categoria.upper()}] {texto}"
        await canal_log.send(log_entry)

    except Exception as e:
        print(f"Error al registrar log: {e}")

async def log_error(bot, contexto: str, error: Exception):
    """Registra errores que ocurran durante eventos del bot."""
    mensaje = f"❗ Error en {contexto}: {str(error)}"
    await registrar_log(bot, mensaje, categoria="errores")

async def log_accion(bot, usuario: discord.Member, accion: str, extra: str = "", categoria: str = "acciones"):
    """Registra una acción específica realizada por un usuario."""
    try:
        texto = f"{usuario.name}#{usuario.discriminator} → {accion}"
        if extra:
            texto += f" | {extra}"
        await registrar_log(bot, texto, categoria)
    except Exception as e:
        await log_error(bot, "log_accion", e)
