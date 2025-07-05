# utils/logger.py
import discord
from datetime import datetime, timezone
import logging
from config import CANAL_LOGS_ID

logger = logging.getLogger("VXbot")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s'))
    logger.addHandler(handler)

async def log_discord(bot, mensaje, nivel="info", titulo=None, extra=None):
    color_map = {
        "info": discord.Color.blurple(),
        "success": discord.Color.green(),
        "warning": discord.Color.orange(),
        "error": discord.Color.red(),
        "critical": discord.Color.dark_red(),
    }
    color = color_map.get(nivel, discord.Color.greyple())
    embed = discord.Embed(
        title=titulo or "Log del sistema",
        description=mensaje,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    if extra:
        for k, v in extra.items():
            embed.add_field(name=k, value=v, inline=False)

    # Railway/Consola
    if nivel == "error":
        logger.error(mensaje)
    elif nivel == "warning":
        logger.warning(mensaje)
    elif nivel == "success":
        logger.info(mensaje)
    else:
        logger.info(mensaje)

    # Discord (canal logs)
    canal_logs = bot.get_channel(CANAL_LOGS_ID)
    if canal_logs:
        try:
            await canal_logs.send(embed=embed)
        except Exception as e:
            logger.error(f"❌ No se pudo enviar log a Discord: {e}")
