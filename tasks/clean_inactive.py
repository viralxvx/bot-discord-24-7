# tasks/clean_inactive.py

import asyncio
import datetime
from discord.ext import tasks
from config import CANAL_SOPORTE
from redis_database import redis
from discord_bot import bot

@tasks.loop(minutes=10)
async def clean_inactive_conversations():
    await bot.wait_until_ready()
    canal_soporte = None

    for guild in bot.guilds:
        canal_soporte = discord.utils.get(guild.text_channels, name=CANAL_SOPORTE)
        if canal_soporte:
            break

    if not canal_soporte:
        return

    now = datetime.datetime.utcnow()
    keys = await redis.keys("convo:*")

    for key in keys:
        data = await redis.hgetall(key)
        last_time_str = data.get("last_time")
        if not last_time_str:
            continue

        try:
            last_time = datetime.datetime.fromisoformat(last_time_str)
        except ValueError:
            continue

        if (now - last_time).total_seconds() > 600:  # 10 minutos
            msg_ids = data.get("message_ids", "").split(",")
            for msg_id in msg_ids:
                try:
                    msg = await canal_soporte.fetch_message(int(msg_id))
                    await msg.delete()
                except:
                    pass
            await redis.delete(key)
