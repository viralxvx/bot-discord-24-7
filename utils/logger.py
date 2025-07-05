import discord
import logging
import os

# Obtener el ID del canal de logs desde la variable de entorno
CANAL_LOGS = int(os.getenv("CANAL_LOGS"))

# Crear un logger centralizado
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)  # Esto es para que los logs importantes se registren

# Crear un manejador para logs de consola (Railway)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Crear un formateador para los logs
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)

# Agregar el manejador a nuestro logger
logger.addHandler(console_handler)

# Variable global para almacenar el mensaje de log
log_message = None

# Función para loguear los mensajes en el canal de Discord
async def log_discord(bot, message, status="Cargando el bot", title="Resumen de inicio del bot"):
    global log_message

    # Obtener el canal de logs usando la variable de entorno
    log_channel = bot.get_channel(CANAL_LOGS)  # Usará el ID del canal de logs desde la variable de entorno
    if log_channel:
        embed = discord.Embed(
            title=title,
            description=message,
            color=discord.Color.green() if status == "Activo" else discord.Color.red()
        )
        embed.set_footer(text=f"Status: {status}")

        if log_message is None:
            # Si no existe el mensaje, crear uno nuevo
            log_message = await log_channel.send(embed=embed)
        else:
            # Si el mensaje ya existe, actualizarlo
            await log_message.edit(embed=embed)

    return log_message  # Devolvemos el mensaje creado o editado

# Función para manejar los logs de Railway y Discord
def custom_log(bot, status, message, title=""):
    if status == "warning":
        logger.warning(message)
    elif status == "info":
        logger.info(message)
    elif status == "error":
        logger.error(message)
    else:
        logger.debug(message)

    # Loguear en Discord también si el bot está disponible
    if bot:
        return bot.loop.create_task(log_discord(bot, message, status, title))  # Devolver la tarea que se crea
