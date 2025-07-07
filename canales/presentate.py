"""
========================================================================================
 Archivo: canales/presentate.py
 Autor:    Viral X | VXbot (Miguel Peralta & ChatGPT)
 Creado:   2025-07
----------------------------------------------------------------------------------------
 PROPÓSITO:
 - Gestiona el canal 👉preséntate para dar la bienvenida profesional y orientar a los 
   nuevos miembros del servidor con un mensaje visual, botones y enlaces útiles.

 NOTA: Todos los textos y descripciones se centralizan en mensajes/presentate_mensaje.py
========================================================================================
"""

import discord
from discord.ext import commands
from config import CANAL_PRESENTATE, GUILD_ID
from mensajes.presentate_mensaje import (
    TITULO_BIENVENIDA,
    DESCRIPCION_BIENVENIDA,
    ENLACES_MENU,
    FOOTER_BIENVENIDA
)

async def limpiar_canal_presentate(bot):
    """Elimina todos los mensajes del canal 👉preséntate (excepto el propio del bot si existe)."""
    canal = bot.get_channel(CANAL_PRESENTATE)
    if canal is None:
        print(f"Error: No se encontró el canal con ID {CANAL_PRESENTATE}")
        return
    try:
        async for mensaje in canal.history(limit=100):
            await mensaje.delete()
    except Exception as e:
        print(f"[ERROR] Al limpiar el canal 👉preséntate: {e}")

async def publicar_bienvenida(bot):
    """Publica el mensaje de bienvenida fijo y con menú de botones/enlaces."""
    canal = bot.get_channel(CANAL_PRESENTATE)
    if canal is None:
        print(f"Error: No se encontró el canal con ID {CANAL_PRESENTATE}")
        return

    embed = discord.Embed(
        title=TITULO_BIENVENIDA,
        description=DESCRIPCION_BIENVENIDA,
        color=discord.Color.blue()
    )
    embed.set_footer(text=FOOTER_BIENVENIDA)
    # Puedes añadir una imagen si lo deseas:
    # embed.set_image(url="URL_IMAGEN")

    # Crea botones/enlaces
    view = discord.ui.View(timeout=None)
    for nombre, url, emoji in ENLACES_MENU:
        view.add_item(discord.ui.Button(label=nombre, url=url, emoji=emoji, style=discord.ButtonStyle.link))

    # Publicar el mensaje y fijarlo
    mensaje = await canal.send(embed=embed, view=view)
    await mensaje.pin()

async def setup(bot):
    print("⚙️ Iniciando módulo del canal 👉preséntate...")
    await limpiar_canal_presentate(bot)
    await publicar_bienvenida(bot)
    print("✅ Canal 👉preséntate configurado.")
