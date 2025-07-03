import discord
from discord.ext import commands
from discord import app_commands

async def estado(interaction: discord.Interaction):
    await interaction.response.send_message("✅ El comando básico está funcionando.")

def setup(bot):
    bot.tree.add_command(app_commands.Command(
        name="estado",
        description="Test directo sin clase",
        callback=estado
    ))
