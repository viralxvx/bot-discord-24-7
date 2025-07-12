import discord
from discord.ext import commands
from discord import app_commands
from config import ADMIN_ID
from utils.panel_embed import actualizar_panel_faltas

class ForzarPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="forzar_panel",
        description="Crea o actualiza el panel de faltas de un usuario manualmente (solo admin)."
    )
    @app_commands.describe(usuario="Usuario al que forzar el panel")
    async def forzar_panel(self, interaction: discord.Interaction, usuario: discord.Member):
        if interaction.user.id != int(ADMIN_ID):
            await interaction.response.send_message(
                "❌ Solo el administrador puede ejecutar este comando.",
                ephemeral=True
            )
            return

        # Llama al panel premium para este usuario, aunque no tenga historial
        try:
            await actualizar_panel_faltas(self.bot, usuario)
            await interaction.response.send_message(
                f"✅ Panel de {usuario.display_name} actualizado o creado en 📤faltas.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creando panel: {e}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ForzarPanel(bot))
