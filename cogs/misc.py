import discord
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="ping", description="Verifica la latencia del bot.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latencia: {latency}ms", ephemeral=True)

    @discord.app_commands.command(name="saludo", description="Envía un saludo amigable.")
    async def saludo(self, interaction: discord.Interaction):
        await interaction.response.send_message("¡Hola! Soy VXbot, siempre listo para ayudarte.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Misc(bot))
