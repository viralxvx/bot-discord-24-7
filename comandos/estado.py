import discord
from discord import app_commands
from discord.ext import commands

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Comando de prueba temporal")
    async def estado(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ El comando `/estado` está funcionando correctamente.")

async def setup(bot):
    await bot.add_cog(Estado(bot))
