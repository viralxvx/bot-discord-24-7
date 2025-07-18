# telegram/limpieza.py
import os
import redis
import asyncio
from datetime import datetime, timedelta

REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# CONFIGURACIÓN
TIEMPO_ATASCADO_HRS = 24         # Horas para enviar recordatorio
TIEMPO_MAXIMO_HRS = 72           # Horas antes de eliminar o resetear
MENSAJE_RECORDATORIO = "👋 ¿Sigues ahí? Recuerda completar tu acceso a VX. Si tienes problemas, responde o usa /start."

async def limpieza_usuarios():
    print("🔎 Iniciando limpieza de usuarios atascados/inactivos...")
    keys = redis_client.keys("user:telegram:*")
    now = datetime.utcnow()
    for key in keys:
        data = redis_client.hgetall(key)
        last_update = data.get("last_update")
        state = data.get("state", "")
        user_id = key.split(":")[-1]
        if not last_update:
            continue
        dt_last = datetime.fromisoformat(last_update)
        horas = (now - dt_last).total_seconds() / 3600

        if state != "whop_ok":
            if TIEMPO_ATASCADO_HRS < horas < TIEMPO_MAXIMO_HRS:
                # Enviar recordatorio (puedes usar aiogram para enviar mensaje)
                print(f"[RECORDATORIO] Usuario {user_id} lleva {int(horas)}h atascado. Enviando recordatorio...")
                # await bot.send_message(user_id, MENSAJE_RECORDATORIO)
            elif horas >= TIEMPO_MAXIMO_HRS:
                # Eliminar usuario de Redis (o marcar como eliminado)
                print(f"[ELIMINAR] Usuario {user_id} lleva {int(horas)}h atascado. Eliminando registro...")
                redis_client.delete(key)
    print("✅ Limpieza completada.")

if __name__ == "__main__":
    asyncio.run(limpieza_usuarios())
