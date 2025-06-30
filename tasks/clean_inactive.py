from discord.ext import tasks
import datetime
from discord_bot import bot
from config import CANAL_SOPORTE, INACTIVITY_TIMEOUT
from state_management import active_conversations, save_state

@tasks.loop(minutes=1)
async def clean_inactive_conversations():
    canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
    if not canal_soporte:
        return
        
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(active_conversations.items()):
        last_message_time = data.get("last_time")
        message_ids = data.get("message_ids", [])
        if last_message_time and (ahora - last_message_time).total_seconds() > INACTIVITY_TIMEOUT:
            for msg_id in message_ids:
                try:
                    msg = await canal_soporte.fetch_message(msg_id)
                    await msg.delete()
                except:
                    pass
            del active_conversations[user_id]
    save_state()
