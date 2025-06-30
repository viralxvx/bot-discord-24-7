from discord.ext import tasks
import datetime
from redis_database import redis

@tasks.loop(hours=24)
async def reset_faltas():
    from discord_bot import bot  # Evita import circular
    await bot.wait_until_ready()

    hoy = datetime.datetime.utcnow().weekday()
    if hoy == 0:  # Lunes
        keys = await redis.keys("faltas:*")
        for key in keys:
            await redis.delete(key)
