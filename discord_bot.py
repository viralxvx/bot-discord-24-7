import discord
from discord.ext import commands

intents = discord.Intents.all()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
