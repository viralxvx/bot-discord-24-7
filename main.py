import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN
from canales.go_viral import setup as go_viral_setup

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    go_viral_setup(bot)  # Configura el canal go-viral

async def main():
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
