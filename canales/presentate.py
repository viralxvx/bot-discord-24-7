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
    GUILD_ID,
    CANAL_GUIAS_ID,
    CANAL_NORMAS_ID,
    CANAL_VICTORIAS_ID,
    CANAL_ESTRATEGIAS_ID,
    CANAL_ENTRENAMIENTO_ID
)
from mensajes.presentate_mensaje import (
    TITULO_BIENVENIDA,
    DESCRIPCION_BIENVENIDA,
    ENLACES_MENU,
    FOOTER_BIENVENIDA
)

REDIS_KEY = "presentate:mensaje_id"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

CANAL_IDS = {
    "guild": GUILD_ID,
    "canal_guias": CANAL_GUIAS_ID,
    "canal_normas": CANAL_NORMAS_ID,
    "canal_victorias": CANAL_VICTORIAS_ID,
    "canal_estrategias": CANAL_ESTRATEGIAS_ID,
    "canal_entrenamiento": CANAL_ENTRENAMIENTO_ID,
}

def reemplazar_placeholders(url: str) -> str:
    for key, value in CANAL_IDS.items():
        url = url.replace(f"{{{key}}}", str(value))
    return url

class MenuBienvenidaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for nombre, url, emoji in ENLACES_MENU:
            url_final = reemplazar_placeholders(url)
            self.add_item(
                discord.ui.Button(
                    label=nombre,
                    url=url_final,
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

async def enviar_bienvenida_dm(member: discord.Member):
    """Envía el mensaje de bienvenida con menú por DM al usuario nuevo."""
    try:
        embed = discord.Embed(
            title=TITULO_BIENVENIDA,
            description=DESCRIPCION_BIENVENIDA,
            color=discord.Color.blue()
        )
        embed.set_footer(text=FOOTER_BIENVENIDA)
        view = MenuBienvenidaView()
        await member.send(embed=embed, view=view)
        print(f"✅ DM de bienvenida enviado a {member.display_name} ({member.id})")
    except Exception as e:
        print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

async def setup(bot):
    print("⚙️ Iniciando módulo del canal 👉preséntate...")
    canal = bot.get_channel(CANAL_PRESENTATE_ID)
    if canal is None:
        print(f"Error: No se encontró el canal con ID {CANAL_PRESENTATE_ID}")
        return

    mensaje_id = redis_client.get(REDIS_KEY)
    mensaje = None

    if mensaje_id:
        try:
            mensaje = await canal.fetch_message(int(mensaje_id))
            embed = discord.Embed(
                title=TITULO_BIENVENIDA,
                description=DESCRIPCION_BIENVENIDA,
                color=discord.Color.blue()
            )
            embed.set_footer(text=FOOTER_BIENVENIDA)
            view = MenuBienvenidaView()
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
        view = MenuBienvenidaView()
        mensaje = await canal.send(embed=embed, view=view)
        await mensaje.pin()
        redis_client.set(REDIS_KEY, mensaje.id)
        print("✅ Mensaje de bienvenida publicado y guardado en Redis.")

    print("✅ Canal 👉preséntate listo a prueba de reinicios.")

    # --- REGISTRA EL EVENTO DE BIENVENIDA ---

    @bot.event
    async def on_member_join(member):
        # Evita que se dispare en otros servidores si el bot está en varios
        if member.guild.id != GUILD_ID:
            return
        await enviar_bienvenida_dm(member)
