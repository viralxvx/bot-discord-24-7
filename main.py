import logging
import asyncio
from discord_bot import bot
from config import TOKEN
from events import on_ready, on_member, on_message

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Registrar eventos
@bot.event
async def on_ready():
    await on_ready.handle_on_ready(bot)

@bot.event
async def on_member_join(member):
    await on_member.handle_member_join(member)

@bot.event
async def on_member_remove(member):
    await on_member.handle_member_remove(member)

@bot.event
async def on_message(message):
    await on_message.handle_on_message(bot, message)

if __name__ == "__main__":
    bot.run(TOKEN)
