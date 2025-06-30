# tasks/verificar_inactividad.py

import datetime
from discord.ext import tasks
from discord_bot import bot
from config import CANAL_FALTAS, TIEMPO_INACTIVIDAD_MAXIMO
from handlers.faltas import faltas_dict, actualizar_mensaje_faltas

@tasks.loop(minutes=60)
async def verificar_inactividad():
    await bot.wait_until_ready()
    ahora = datetime.datetime.now(datetime.timezone.utc)
    canal_faltas = None

    for guild in bot.guilds:
        canal_faltas = discord.utils.get(guild.text_channels, name=CANAL_FALTAS)
        if canal_faltas:
            break

    if not canal_faltas:
        return

    for user_id, datos in faltas_dict.items():
        ultima_falta = datos.get("ultima_falta_time")
        if ultima_falta is None:
            continue
        diferencia = ahora - ultima_falta
        if diferencia.total_seconds() > TIEMPO_INACTIVIDAD_MAXIMO:
            # Marcar usuario como inactivo o tomar acción
            datos["estado"] = "Inactivo"
            user = bot.get_user(user_id)
            if user:
                await actualizar_mensaje_faltas(canal_faltas, user, datos["faltas"], datos["aciertos"], "Inactivo")
