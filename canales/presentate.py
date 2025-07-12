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
    MENU_DESPLEGABLE,
    FOOTER_BIENVENIDA
)

# Ya NO necesitas guardar mensaje_id en Redis porque cada mensaje es único

CANAL_IDS = {
    "CANAL_GUIAS_ID": CANAL_GUIAS_ID,
    "CANAL_NORMAS_ID": CANAL_NORMAS_ID,
    "CANAL_VICTORIAS_ID": CANAL_VICTORIAS_ID,
    "CANAL_ESTRATEGIAS_ID": CANAL_ESTRATEGIAS_ID,
    "CANAL_ENTRENAMIENTO_ID": CANAL_ENTRENAMIENTO_ID,
}

class MenuDesplegable(discord.ui.Select):
    def __init__(self, guild_id):
        options = [
            discord.SelectOption(
                label=label,
                description=desc,
                emoji=emoji
            )
            for (label, desc, canal_key, emoji) in MENU_DESPLEGABLE
        ]
        super().__init__(
            placeholder="Selecciona un recurso para ir directo...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="menu_presentate"
        )
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        for (label, desc, canal_key, emoji) in MENU_DESPLEGABLE:
            if label == selected:
                canal_id = CANAL_IDS[canal_key]
                url = f"https://discord.com/channels/{self.guild_id}/{canal_id}"
                await interaction.response.send_message(
                    f"🔗 Aquí tienes el acceso directo a **{label}**: {url}",
                    ephemeral=True  # Solo lo ve el usuario que seleccionó
                )
                break

class MenuDesplegableView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.add_item(MenuDesplegable(guild_id))

async def enviar_bienvenida_canal(bot, member: discord.Member):
    canal = bot.get_channel(CANAL_PRESENTATE_ID)
    if canal is None:
        print(f"Error: No se encontró el canal con ID {CANAL_PRESENTATE_ID}")
        return

    guild_id = canal.guild.id
    embed_desc = f"{member.mention}\n\n{DESCRIPCION_BIENVENIDA}"

    embed = discord.Embed(
        title=TITULO_BIENVENIDA,
        description=embed_desc,
        color=discord.Color.blue()
    )
    embed.set_footer(text=FOOTER_BIENVENIDA)
    view = MenuDesplegableView(guild_id)

    mensaje = await canal.send(embed=embed, view=view)
    await mensaje.pin()
    print(f"✅ Mensaje de bienvenida personalizado publicado para {member.display_name}")

async def enviar_bienvenida_dm(member: discord.Member):
    try:
        guild_id = member.guild.id
        embed = discord.Embed(
            title=TITULO_BIENVENIDA,
            description=DESCRIPCION_BIENVENIDA,
            color=discord.Color.blue()
        )
        embed.set_footer(text=FOOTER_BIENVENIDA)
        view = MenuDesplegableView(guild_id)
        await member.send(embed=embed, view=view)
        print(f"✅ DM de bienvenida enviado a {member.display_name}")
    except Exception as e:
        print(f"⚠️ No se pudo enviar DM a {member.display_name}: {e}")

async def setup(bot):
    print("⚙️ Iniciando módulo del canal 👉preséntate...")

    @bot.event
    async def on_member_join(member):
        if member.guild.id != GUILD_ID:
            return
        await enviar_bienvenida_canal(bot, member)
        await enviar_bienvenida_dm(member)

    print("✅ Canal 👉preséntate listo: bienvenida personalizada para cada usuario y menú desplegable profesional.")
