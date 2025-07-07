"""
========================================================================================
 Archivo: canales/presentate.py
 Autor:    Viral X | VXbot (Miguel Peralta & ChatGPT)
----------------------------------------------------------------------------------------
 PROPÓSITO:
 Gestiona el canal 👉preséntate para dar la bienvenida profesional y orientar a los 
 nuevos miembros del servidor con un mensaje visual, botones y enlaces útiles.
 Mantiene el menú siempre funcional, incluso tras reinicios, guardando el ID en Redis.

 TODOS LOS TEXTOS en mensajes/presentate_mensaje.py
========================================================================================
"""

import discord
from discord.ext import commands
import redis
from config import (
    CANAL_PRESENTATE_ID,
    REDIS_URL,
    CANAL_GUIAS_ID,
    CANAL_NORMAS_ID,
    CANAL_VICTORIAS_ID,
    CANAL_ESTRATEGIAS_ID,
    CANAL_ENTRENAMIENTO_ID,
)
from mensajes.presentate_mensaje import (
    TITULO_BIENVENIDA,
    DESCRIPCION_BIENVENIDA,
    FOOTER_BIENVENIDA
)

REDIS_KEY = "presentate:mensaje_id"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def build_menu_links(guild_id):
    return [
        ("📖 Guías", f"https://discord.com/channels/{guild_id}/{CANAL_GUIAS_ID}", "📖"),
        ("✅ Normas", f"https://discord.com/channels/{guild_id}/{CANAL_NORMAS_ID}", "✅"),
        ("🏆 Victorias", f"https://discord.com/channels/{guild_id}/{CANAL_VICTORIAS_ID}", "🏆"),
        ("♟ Estrategias", f"https://discord.com/channels/{guild_id}/{CANAL_ESTRATEGIAS_ID}", "♟"),
        ("🏋 Entrenamiento", f"https://discord.com/channels/{guild_id}/{CANAL_ENTRENAMIENTO_ID}", "🏋"),
    ]

class MenuBienvenidaView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        for nombre, url, emoji in build_menu_links(guild_id):
            self.add_item(
                discord.ui.Button(
                    label=nombre,
                    url=url,
                    emoji=emoji,
                    style=discord.ButtonStyle.link
                )
            )

async def limpiar_canal_presentate(canal, mensaje_id_actual=None):
    async for mensaje in canal.history(limit=100):
        if mensaje_id_actual and mensaje.id == int(mensaje_id_actual):
            continue
        try:
            await mensaje.delete()
        except Exception:
            pass

async def setup(bot):
    print("⚙️ Iniciando módulo del canal 👉preséntate...")
    canal = bot.get_channel(CANAL_PRESENTATE_ID)
    if canal is None:
        print(f"Error: No se encontró el canal con ID {CANAL_PRESENTATE_ID}")
        return

    mensaje_id = redis_client.get(REDIS_KEY)
    mensaje = None
    guild_id = canal.guild.id

    if mensaje_id:
        try:
            mensaje = await canal.fetch_message(int(mensaje_id))
            embed = discord.Embed(
                title=TITULO_BIENVENIDA,
                description=DESCRIPCION_BIENVENIDA,
                color=discord.Color.blue()
            )
            embed.set_footer(text=FOOTER_BIENVENIDA)
            view = MenuBienvenidaView(guild_id)
            await mensaje.edit(embed=embed, view=view)
            await mensaje.pin()
            print("🔁 Mensaje de bienvenida actualizado y menú reactivado tras reinicio.")
        except discord.NotFound:
            mensaje = None

    if not mensaje:
        await limpiar_canal_presentate(canal)
        embed = discord.Embed(
            title=TITULO_BIENVENIDA,
            description=DESCRIPCION_BIENVENIDA,
            color=discord.Color.blue()
        )
        embed.set_footer(text=FOOTER_BIENVENIDA)
        view = MenuBienvenidaView(guild_id)
        mensaje = await canal.send(embed=embed, view=view)
        await mensaje.pin()
        redis_client.set(REDIS_KEY, mensaje.id)
        print("✅ Mensaje de bienvenida publicado y guardado en Redis.")

    print("✅ Canal 👉preséntate listo a prueba de reinicios.")
