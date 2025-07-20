# main.py

import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, GUILD_ID
from comandos import idea_viral

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🤖 Asistente de hilos virales activo. Comandos sincronizados: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"❌ Error al sincronizar comandos: {e}")

async def setup():
    await bot.add_cog(idea_viral.IdeaViral(bot))

bot.loop.create_task(setup())
bot.run(DISCORD_TOKEN)
