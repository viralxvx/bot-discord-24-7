import discord
import datetime
from discord_bot import bot
from config import CANAL_SOPORTE, MENSAJE_NORMAS
from state_management import active_conversations, faltas_dict, save_state
from utils import actualizar_mensaje_faltas
from views import SupportMenu

async def handle_soporte_message(message):
    if message.author.bot:
        return
        
    user_id = message.author.id
    if user_id not in active_conversations:
        active_conversations[user_id] = {"message_ids": [], "last_time": datetime.datetime.now(datetime.timezone.utc)}
            
    if message.content.lower() in ["salir", "cancelar", "fin", "ver reglas"]:
        if message.content.lower() == "ver reglas":
            msg = await message.channel.send(MENSAJE_NORMAS)
            active_conversations[user_id]["message_ids"].append(msg.id)
            active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
            faltas_dict[user_id]["aciertos"] += 1
            canal_faltas = discord.utils.get(message.guild.text_channels, name="📤faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[user_id]["faltas"], faltas_dict[user_id]["aciertos"], faltas_dict[user_id]["estado"])
        else:
            msg = await message.channel.send("✅ **Consulta cerrada**")
            active_conversations[user_id]["message_ids"].append(msg.id)
            active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
        await message.delete()
        return
            
    msg = await message.channel.send("👋 **Selecciona una opción**", view=SupportMenu(message.author, message.content))
    active_conversations[user_id]["message_ids"].append(msg.id)
    active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
    await message.delete()
