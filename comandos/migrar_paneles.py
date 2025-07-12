import discord
from discord.ext import commands
from discord import app_commands
from config import ADMIN_ID
from utils.panel_embed import actualizar_panel_faltas

class MigrarPaneles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="migrar_paneles",
        description="Migra TODOS los paneles públicos al nuevo formato premium (solo admin)."
    )
    async def migrar_paneles(self, interaction: discord.Interaction):
        if interaction.user.id != int(ADMIN_ID):
            await interaction.response.send_message(
                "❌ Solo el administrador puede ejecutar este comando.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔄 Migrando paneles públicos a formato premium... Esto puede tardar unos segundos.",
            ephemeral=True
        )

        guild = interaction.guild
        miembros = [m for m in guild.members if not m.bot]

        migrados = 0
        errores = []
        for miembro in miembros:
            try:
                await actualizar_panel_faltas(self.bot, miembro)
                migrados += 1
            except Exception as e:
                errores.append(f"{miembro.display_name}: {e}")

        msg = f"✅ Paneles migrados: {migrados}."
        if errores:
            msg += f"\n❌ Errores:\n" + "\n".join(errores[:5])  # solo primeros 5

        await interaction.followup.send(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MigrarPaneles(bot))
