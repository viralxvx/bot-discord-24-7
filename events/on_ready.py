import datetime
import discord
from utils import registrar_log

async def on_ready(bot):
    print(f"{bot.user} está listo y conectado.")
    await registrar_log(f"🤖 Bot iniciado: {bot.user}", categoria="sistema")
    # Aquí puedes agregar otras tareas que quieras hacer al iniciar el bot, por ejemplo, limpiar estados antiguos, inicializar cachés, etc.
