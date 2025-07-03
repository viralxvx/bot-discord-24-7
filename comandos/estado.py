import discord
from discord.ext import commands
from discord import app_commands

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema de faltas.")
    async def estado(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "✅ Comando `/estado` funcionando correctamente.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Estado(bot))
