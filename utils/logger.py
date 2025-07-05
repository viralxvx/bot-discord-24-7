import discord
import logging
import os
import aiohttp
from discord import Webhook
from datetime import datetime, timezone

# URL del webhook desde variable de entorno
WEB_HOOKS_CANAL_LOGS = os.getenv("WEB_HOOKS_CANAL_LOGS")

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

# Mensaje persistente para editar si es necesario
log_message_id = None

# ✅ FUNCIÓN PRINCIPAL: Log en Discord vía Webhook + consola
async def log_discord(bot, message: str, status: str = "Cargando", title: str = "Resumen de inicio del bot"):
    global log_message_id

    # Log en consola (Railway)
    print(f"[{status}] {title}: {message}")

    color = (
        discord.Color.green() if status.lower() in ["activo", "success"] else
        discord.Color.red() if status.lower() in ["error"] else
        discord.Color.orange()
    )

    embed = discord.Embed(title=title, description=message, color=color)
    embed.set_footer(text=f"Status: {status}")
    embed.timestamp = datetime.now(timezone.utc)

    try:
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(WEB_HOOKS_CANAL_LOGS, session=session)

            if log_message_id:
                try:
                    await webhook.edit_message(log_message_id, embed=embed)
                except:
                    # Si falló editar, crea uno nuevo y actualiza log_message_id
                    msg = await webhook.send(embed=embed, wait=True)
                    log_message_id = msg.id
            else:
                msg = await webhook.send(embed=embed, wait=True)
                log_message_id = msg.id
    except Exception as e:
        print(f"❌ Error enviando log a Discord vía webhook: {e}")

    return log_message_id

# ✅ OPCIONAL: Log desde otros lugares (automático en Discord y consola)
def custom_log(bot, level: str, message: str, title: str = "Log"):
    if level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.info(message)

    if bot:
        status = "Error" if level == "error" else "Advertencia" if level == "warning" else "Activo"
        return bot.loop.create_task(log_discord(bot, message, status, title))
