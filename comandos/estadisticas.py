import discord
from discord.ext import commands
from discord import app_commands

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estadisticas", description="Muestra estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "📊 Comando `/estadisticas` funcionando correctamente.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
