import discord
from .logs import registrar_log

CANAL_X_NORMAS = "𝕏-normas"

async def manejar_x_normas(message, bot):
    if message.channel.name == CANAL_X_NORMAS and not message.author.bot:
        await registrar_log(f"Norma X actualizada por {message.author.name}", categoria="x_normas")
