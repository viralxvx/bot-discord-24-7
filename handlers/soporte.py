import discord
from .logs import registrar_log

CANAL_SOPORTE = "👨🔧soporte"
active_conversations = {}

async def manejar_soporte(message, bot):
    user_id = message.author.id
    if user_id not in active_conversations:
        active_conversations[user_id] = {"message_ids": [], "last_time": datetime.datetime.now(datetime.timezone.utc)}
    await registrar_log(f"Soporte solicitado por {message.author.name}", categoria="soporte")
