import discord
from handlers.logs import registrar_log

CANAL_ANUNCIOS = "🔔anuncios"

async def manejar_normas_generales(message: discord.Message):
    canal_anuncios = discord.utils.get(message.guild.text_channels, name=CANAL_ANUNCIOS)
    if canal_anuncios:
        await canal_anuncios.send(f"📢 **Norma actualizada**: {message.channel.mention}")
        await registrar_log(f"Norma publicada desde {message.channel.name}", categoria="normas")
