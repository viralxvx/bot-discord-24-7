from discord.ext import commands, tasks
import discord
from config import TOKEN, intents

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

from utils import registrar_log

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    await registrar_log(f"Bot iniciado")

@bot.event
async def on_member_remove(member):
    await registrar_log(f"👋 Miembro salió: {member.name}", categoria="miembros")
