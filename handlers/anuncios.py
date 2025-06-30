import discord
from utils import publicar_mensaje_unico
from config import CANAL_ANUNCIOS, MENSAJE_ANUNCIO_PERMISOS

async def handle_anuncios(message):
    if message.channel.name != CANAL_ANUNCIOS or message.author.bot:
        return
        
    # Publicar mensaje único en anuncios
    await publicar_mensaje_unico(message.channel, MENSAJE_ANUNCIO_PERMISOS)
