import os
import json
import asyncio
import aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis = None

async def connect_redis():
    global redis
    if not redis:
        redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    return redis

async def save_state(state: dict):
    """
    Guarda el estado completo en Redis en formato JSON.
    """
    r = await connect_redis()
    try:
        state_json = json.dumps(state)
        await r.set("bot_state", state_json)
    except Exception as e:
        print(f"[Redis] Error guardando estado: {e}")

async def load_state():
    """
    Carga el estado completo desde Redis y lo devuelve como dict.
    Si no existe, devuelve dict vacío.
    """
    r = await connect_redis()
    try:
        state_json = await r.get("bot_state")
        if state_json:
            return json.loads(state_json)
        return {}
    except Exception as e:
        print(f"[Redis] Error cargando estado: {e}")
        return {}

async def clear_state():
    """
    Borra el estado guardado en Redis.
    """
    r = await connect_redis()
    try:
        await r.delete("bot_state")
    except Exception as e:
        print(f"[Redis] Error borrando estado: {e}")
