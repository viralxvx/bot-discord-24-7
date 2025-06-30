import datetime
from discord.ext import tasks
import discord
from redis_database import redis
from config import CANAL_SOPORTE

@tasks.loop(minutes=10)
async def clean_inactive():
    from discord_bot import bot  # Evita import circular
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

        if (now - last_time).total_seconds() > 600:
            msg_ids = data.get("message_ids", "").split(",")
            for msg_id in msg_ids:
                try:
                    msg = await canal_soporte.fetch_message(int(msg_id))
                    await msg.delete()
                except:
                    pass
            await redis.delete(key)
