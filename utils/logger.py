import discord
import logging
import os

# ID del canal de logs desde variable de entorno
CANAL_LOGS = int(os.getenv("CANAL_LOGS"))

# Configuración del logger de consola (para Railway)
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Mensaje persistente para editar (en Discord)
log_message = None


# ✅ FUNCIÓN PRINCIPAL: Log en Discord + Consola
async def log_discord(bot, message: str, status: str = "Cargando", title: str = "Resumen de inicio del bot"):
    global log_message

    # También mostrar en consola (Railway)
    print(f"[{status}] {title}: {message}")

    canal_logs = bot.get_channel(CANAL_LOGS)
    if not canal_logs:
        print("❌ Canal de logs no encontrado.")
        return

    color = discord.Color.green() if status == "Activo" or status == "success" else (
        discord.Color.red() if status == "Error" or status == "error" else discord.Color.orange()
    )

    embed = discord.Embed(
        title=title,
        description=message,
        color=color
    )
    embed.set_footer(text=f"Status: {status}")

    try:
        if log_message is None:
            log_message = await canal_logs.send(embed=embed)
        else:
            await log_message.edit(embed=embed)
    except Exception as e:
        print(f"❌ Error enviando log a Discord: {e}")

    return log_message


# ✅ OPCIONAL: Log desde otros lugares (automático en Discord y consola)
def custom_log(bot, level: str, message: str, title: str = "Log"):
    # Log en consola
    if level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.info(message)

    # También log en Discord (si hay bot disponible)
    if bot:
        status = "Error" if level == "error" else "Advertencia" if level == "warning" else "Activo"
        return bot.loop.create_task(log_discord(bot, message, status, title))
