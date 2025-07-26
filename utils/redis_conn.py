# utils/redis_conn.py

import redis
from config import REDIS_URL

try:
    redis_conn = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    redis_conn.ping()
    print("✅ Conexión a Redis exitosa")
except Exception as e:
    raise Exception(f"❌ Error al conectar con Redis: {e}")
