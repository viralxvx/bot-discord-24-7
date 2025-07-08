import os
import redis

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    print("ERROR: No se encontró la variable de entorno REDIS_URL")
    exit(1)

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

for key in r.scan_iter("go_viral:apoyos:*"):
    usuarios = r.smembers(key)
    print(f"{key}: {usuarios}")
