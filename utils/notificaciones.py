# utils/notificaciones.py

import redis.asyncio as aioredis
from config import REDIS_URL
from datetime import datetime, timedelta

KEY_NOVEDADES = "vxbot:novedades"
KEY_USER_LEIDOS = "vxbot:leidos:{user_id}"
KEY_USER_LAST_JOIN = "vxbot:last_join:{user_id}"

async def get_redis():
    return aioredis.from_url(REDIS_URL, decode_responses=True)

async def registrar_novedad(update_id, tipo, titulo, descripcion, url, message_id):
    redis = await get_redis()
    await redis.hset(KEY_NOVEDADES, update_id, f"{tipo}|{titulo}|{descripcion}|{url}|{message_id}|{datetime.now().isoformat()}")

async def obtener_no_leidos(user_id):
    redis = await get_redis()
    novedades = await redis.hgetall(KEY_NOVEDADES)
    leidos = await redis.smembers(KEY_USER_LEIDOS.format(user_id=user_id))
    no_leidos = []
    for k, v in novedades.items():
        if k not in leidos:
            tipo, titulo, descripcion, url, msg_id, fecha = v.split("|", 5)
            no_leidos.append({
                "update_id": k, "tipo": tipo, "titulo": titulo, "descripcion": descripcion, "url": url, "fecha": fecha
            })
    return sorted(no_leidos, key=lambda x: x['fecha'], reverse=True)

async def marcar_todo_leido(user_id):
    redis = await get_redis()
    novedades = await redis.hgetall(KEY_NOVEDADES)
    update_ids = list(novedades.keys())
    if update_ids:
        await redis.sadd(KEY_USER_LEIDOS.format(user_id=user_id), *update_ids)

AUSENCIA_DIAS = 7

async def usuario_ausente(user_id):
    redis = await get_redis()
    last = await redis.get(KEY_USER_LAST_JOIN.format(user_id=user_id))
    if not last:
        return False
    last_date = datetime.fromisoformat(last)
    return (datetime.now() - last_date).days >= AUSENCIA_DIAS

async def registrar_reingreso(user_id):
    redis = await get_redis()
    await redis.set(KEY_USER_LAST_JOIN.format(user_id=user_id), datetime.now().isoformat())
