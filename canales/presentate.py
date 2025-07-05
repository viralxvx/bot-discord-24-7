import discord
from discord.ext import commands
from config import (
    CANAL_PRESENTATE_ID,
    CANAL_GUIAS_ID,
    CANAL_NORMAS_ID,
    CANAL_VICTORIAS_ID,
    CANAL_ESTRATEGIAS_ID,
    CANAL_ENTRENAMIENTO_ID,
)
from utils.logger import log_discord

class MenuInicio(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSelect())

class MenuSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="📖 Guías", description="Empieza por aquí", value="guias"),
            discord.SelectOption(label="✅ Normas Generales", description="Lee las reglas", value="normas"),
            discord.SelectOption(label="🏆 Victorias", description="Casos de éxito", value="victorias"),
            discord.SelectOption(label="♟ Estrategias", description="Métodos que funcionan", value="estrategias"),
            discord.SelectOption(label="🏋 Entrenamiento", description="Pide ayuda y participa", value="entrenamiento"),
        ]
        super().__init__(placeholder="Selecciona una sección para empezar", options=options, custom_id="menu_inicio")

    async def callback(self, interaction: discord.Interaction):
        canal_id = {
            "guias": CANAL_GUIAS_ID,
            "normas": CANAL_NORMAS_ID,
            "victorias": CANAL_VICTORIAS_ID,
            "estrategias": CANAL_ESTRATEGIAS_ID,
            "entrenamiento": CANAL_ENTRENAMIENTO_ID,
        }[self.values[0]]

        canal_mention = f"<#{canal_id}>"

        try:
            await interaction.user.send(
                content=f"📌 Has seleccionado {canal_mention}. Haz clic en el botón para ir directo:",
                view=IrAlCanalButton(canal_id)
            )
            await interaction.response.defer()
        except discord.Forbidden:
            await interaction.response.send_message("❌ No pude enviarte un mensaje privado. Activa tus DMs.", ephemeral=True)
            await log_discord(interaction.client, "❌ No se pudo enviar DM a un usuario desde el menú de presentación.", status="warning", title="Presentate")

class IrAlCanalButton(discord.ui.View):
    def __init__(self, canal_id):
        super().__init__()
        self.add_item(discord.ui.Button(
            label="Ir al canal",
            url=f"https://discord.com/channels/1346959710519038003/{canal_id}",
            style=discord.ButtonStyle.link
        ))

class Presentate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def enviar_bienvenida(member: discord.Member, bot):
    canal = bot.get_channel(CANAL_PRESENTATE_ID)
    if not canal:
        await log_discord(bot, f"❌ Canal de presentación no encontrado: {CANAL_PRESENTATE_ID}", status="error", title="Presentate")
        return

    embed = discord.Embed(
        title="👋 ¡Bienvenido/a a Viral 𝕏 | V𝕏!",
        description=(
            "Estamos emocionados de tenerte aquí.\n\n"
            "Aquí tienes los pasos esenciales para integrarte:\n"
            "📖 Lee las guías\n"
            "✅ Revisa las normas\n"
            "🏆 Inspírate con las victorias\n"
            "♟ Estudia las estrategias\n"
            "🏋 Participa en el entrenamiento\n\n"
            "👇 Usa el menú para ir directo a cada sección"
        ),
        color=0x2ecc71
    )
    try:
        embed.set_thumbnail(url=member.display_avatar.url)
    except Exception:
        pass

    try:
        await canal.send(content=member.mention, embed=embed, view=MenuInicio())
        await log_discord(bot, f"👤 Bienvenida enviada a {member.mention} en #preséntate", status="success", title="Presentate")
    except Exception as e:
        await log_discord(bot, f"❌ Error enviando bienvenida a {member.display_name}: {e}", status="error", title="Presentate")

async def setup(bot):
    await bot.add_cog(Presentate(bot))
