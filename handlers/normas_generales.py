import discord
from .logs import registrar_log

CANAL_NORMAS_GENERALES = "✅normas-generales"
MENSAJE_NORMAS = "Por favor, respeta las normas del servidor."

async def manejar_normas_generales(message, bot):
    if message.channel.name == CANAL_NORMAS_GENERALES and not message.author.bot:
        await registrar_log(f"Norma recordada en {message.channel.name} por {message.author.name}", categoria="normas")
