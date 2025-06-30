# tasks/reset_faltas.py

import datetime
from discord.ext import tasks
from discord_bot import bot
from config import CANAL_FALTAS
from handlers.faltas import faltas_dict, actualizar_mensaje_faltas

@tasks.loop(hours=24)
async def resetear_faltas_diarias():
    await bot.wait_until_ready()
    ahora = datetime.datetime.now(datetime.timezone.utc)
    canal_faltas = None

    for guild in bot.guilds:
        canal_faltas = discord.utils.get(guild.text_channels, name=CANAL_FALTAS)
        if canal_faltas:
            break

    if not canal_faltas:
        return

    # Resetear faltas y actualizar mensajes
    for user_id in list(faltas_dict.keys()):
        faltas_dict[user_id]["faltas"] = 0
        faltas_dict[user_id]["aciertos"] = 0
        faltas_dict[user_id]["ultima_falta_time"] = None
        faltas_dict[user_id]["estado"] = "OK"
        user = bot.get_user(user_id)
        if user:
            await actualizar_mensaje_faltas(canal_faltas, user, 0, 0, "OK")
