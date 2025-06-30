# events/on_ready.py
import datetime
from utils import registrar_log

async def on_ready():
    print(f"✅ Bot conectado")
    print(f"Hora UTC: {datetime.datetime.utcnow().isoformat()}")
    await registrar_log("🤖 Bot listo y conectado", categoria="sistema")
