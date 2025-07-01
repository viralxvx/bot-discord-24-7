# main.py

import discord
from discord.ext import commands
import asyncio
import os
from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Importar módulos del bot
from canales import go_viral, logs

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user.name}")
    await go_viral.inicializar(bot)
    await logs.inicializar(bot)

bot.run(TOKEN)
