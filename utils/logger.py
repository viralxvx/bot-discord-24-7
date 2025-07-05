# utils/logger.py

import logging
import discord
from config import CANAL_LOGS_ID

def log_to_railway(mensaje, nivel="info", titulo=None):
    # Nivel puede ser "info", "success", "warning", "error"
    prefijo = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }.get(nivel, "ℹ️")
    texto = f"{prefijo} {titulo + ': ' if titulo else ''}{mensaje}"
    if nivel == "error":
        logging.error(texto)
    elif nivel == "warning":
        logging.warning(texto)
    else:
        logging.info(texto)

async def log_discord(bot, mensaje, nivel="info", titulo=None):
    log_to_railway(mensaje, nivel, titulo)  # Siempre log en consola/Railway

    canal = bot.get_channel(CANAL_LOGS_ID)
    if canal is None:
        # Espera si aún no está listo el bot
        await bot.wait_until_ready()
        canal = bot.get_channel(CANAL_LOGS_ID)
        if canal is None:
            return  # Si aun así no existe, omitir

    color = {
        "info": discord.Color.blue(),
        "success": discord.Color.green(),
        "warning": discord.Color.orange(),
        "error": discord.Color.red()
    }.get(nivel, discord.Color.blue())

    embed = discord.Embed(
        title=titulo or "Log de sistema",
        description=str(mensaje),
        color=color
    )
    await canal.send(embed=embed)
