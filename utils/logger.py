import discord
import logging

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

# Función para loguear los mensajes en el canal de Discord
async def log_discord(bot, message, level="info", title="Log"):
    # Obtener el canal de logs desde las variables de entorno o como está configurado
    log_channel = bot.get_channel(CANAL_LOGS)  # Cambia esto con el ID del canal de logs
    if log_channel:
        embed = discord.Embed(
            title=title,
            description=message,
            color=discord.Color.green() if level == "info" else discord.Color.red()
        )
        embed.set_footer(text=f"Nivel: {level}")
        await log_channel.send(embed=embed)

# Función para manejar los logs de Railway y Discord
def custom_log(bot, level, message, title=""):
    if level == "warning":
        logger.warning(message)
    elif level == "info":
        logger.info(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.debug(message)

    # Loguear en Discord también si el bot está disponible
    if bot:
        bot.loop.create_task(log_discord(bot, message, level, title))
