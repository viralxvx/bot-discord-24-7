import discord
from discord.ext import commands
from config import PREFIX

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)
