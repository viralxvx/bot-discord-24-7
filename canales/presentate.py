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

REDIS_KEY = "presentate:mensaje_id"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

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

async def crear_o_actualizar_mensaje_bienvenida(bot, mention_text=None):
    canal = bot.get_channel(CANAL_PRESENTATE_ID)
    if canal is None:
        print(f"Error: No se encontró el canal con ID {CANAL_PRESENTATE_ID}")
        return

    guild_id = canal.guild.id
    mensaje_id = redis_client.get(REDIS_KEY)
    embed_desc = DESCRIPCION_BIENVENIDA
    if mention_text:
        embed_desc = f"{mention_text}\n\n{DESCRIPCION_BIENVENIDA}"

    embed = discord.Embed(
        title=TITULO_BIENVENIDA,
        description=embed_desc,
        color=discord.Color.blue()
    )
    embed.set_footer(text=FOOTER_BIENVENIDA)
    view = MenuDesplegableView(guild_id)

    mensaje = None
    if mensaje_id:
        try:
            mensaje = await canal.fetch_message(int(mensaje_id))
            await mensaje.edit(embed=embed, view=view)
            await mensaje.pin()
            print("🔁 Mensaje de bienvenida actualizado y menú reactivado tras reinicio.")
        except discord.NotFound:
            mensaje = None

    if not mensaje:
        mensaje = await canal.send(embed=embed, view=view)
        await mensaje.pin()
        redis_client.set(REDIS_KEY, mensaje.id)
        print("✅ Mensaje de bienvenida publicado y guardado en Redis.")

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
    await crear_o_actualizar_mensaje_bienvenida(bot)

    @bot.event
    async def on_member_join(member):
        if member.guild.id != GUILD_ID:
            return
        # Menciona al usuario y lo invita a presentarse (edita el mensaje fijo)
        mention_text = f"🎉 {member.mention} acaba de unirse. ¡Dale la bienvenida y cuéntanos sobre ti!"
        await crear_o_actualizar_mensaje_bienvenida(bot, mention_text=mention_text)
        await enviar_bienvenida_dm(member)

    print("✅ Canal 👉preséntate listo, menú fijo, DM automático y a prueba de reinicio.")
