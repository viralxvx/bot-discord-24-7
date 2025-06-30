import discord
from utils import publicar_mensaje_unico
from config import CANAL_NORMAS_GENERALES, CANAL_ANUNCIOS, MENSAJE_NORMAS

async def handle_normas_message(message):
    if message.author.bot:
        return
        
    canal_anuncios = discord.utils.get(message.guild.text_channels, name=CANAL_ANUNCIOS)
    if canal_anuncios:
        await publicar_mensaje_unico(canal_anuncios, f"📢 **Norma actualizada**: {message.channel.mention}")
