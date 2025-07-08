import os

REDIS_URL = os.getenv("REDIS_URL")


r = redis.from_url(REDIS_URL, decode_responses=True)

# Muestra todos los keys de apoyos
keys = r.keys("go_viral:apoyos:*")
print(f"Claves encontradas: {len(keys)}")

for key in keys:
    usuarios = r.smembers(key)
    print(f"{key} => {usuarios}")

# Opcional: Ver también las validaciones (👍)
keys_valid = r.keys("go_viral:validaciones:*")
for key in keys_valid:
    usuarios = r.smembers(key)
    print(f"{key} => {usuarios}")
