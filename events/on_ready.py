# events/on_ready.py

import datetime
from utils import registrar_log
from discord_bot import bot  # Asegúrate que esta importación no causa ciclos

async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"Hora UTC: {datetime.datetime.utcnow().isoformat()}")
    await registrar_log("🤖 Bot listo y conectado", categoria="sistema")
