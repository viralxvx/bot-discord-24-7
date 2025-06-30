# tasks/limpiar_expulsados.py

import asyncio
from discord.ext import tasks
from discord_bot import bot
from config import CANAL_SOPORTE

@tasks.loop(hours=1)
async def limpiar_mensajes_expulsados():
    await bot.wait_until_ready()
    canal_soporte = None

    for guild in bot.guilds:
        canal_soporte = discord.utils.get(guild.text_channels, name=CANAL_SOPORTE)
        if canal_soporte:
            break

    if not canal_soporte:
        return

    async for message in canal_soporte.history(limit=100):
        if message.author not in message.guild.members:
            try:
                await message.delete()
            except:
                pass
