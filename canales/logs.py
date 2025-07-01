# canales/logs.py

import datetime
import discord
from config import CANAL_LOGS, MAX_LOG_LENGTH
from state_management import save_state

# Asumiendo que el bot está definido en main.py o en otro módulo
# Para evitar el error de importación 'discord_bot', importaremos el bot
# directamente desde main. Si usas otro archivo, ajusta esta línea.
from main import bot

async def registrar_log(texto: str, categoria: str = "general"):
    """Registra una entrada en el canal de logs con categoría y timestamp."""
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
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

async def log_error(contexto: str, error: Exception):
    """Registra errores que ocurran durante eventos del bot."""
    mensaje = f"❗ Error en {contexto}: {str(error)}"
    await registrar_log(mensaje, categoria="errores")

async def log_accion(usuario: discord.Member, accion: str, extra: str = "", categoria: str = "acciones"):
    """Registra una acción específica realizada por un usuario."""
    try:
        texto = f"{usuario.name}#{usuario.discriminator} → {accion}"
        if extra:
            texto += f" | {extra}"
        await registrar_log(texto, categoria)
    except Exception as e:
        await log_error("log_accion", e)

def guardar_estado():
    """Guarda el estado actual de datos persistentes."""
    try:
        save_state()
    except Exception as e:
        print(f"Error guardando estado: {e}")
