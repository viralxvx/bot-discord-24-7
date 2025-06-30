import discord
from .logs import registrar_log

CANAL_ANUNCIOS = "🔔anuncios"

async def manejar_anuncios(message, bot):
    if message.channel.name == CANAL_ANUNCIOS and not message.author.bot:
        await registrar_log(f"Anuncio publicado por {message.author.name}: {message.content}", categoria="anuncios")
