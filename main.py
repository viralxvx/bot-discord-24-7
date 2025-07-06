import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print(f"ID del bot: {bot.user.id}")

# Carga tu módulo go_viral normalmente
async def load_cogs():
    await bot.load_extension("canales.go_viral")

bot.loop.create_task(load_cogs())

bot.run("DISCORD_TOKEN")
