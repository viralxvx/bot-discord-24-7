# discord_bot.py
import discord
from discord.ext import commands
from config import TOKEN, CANAL_OBJETIVO, ADMIN_ID  # otras constantes

intents = discord.Intents.all()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
