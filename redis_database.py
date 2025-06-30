import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

# Crear conexión a Redis
redis_client = redis.from_url(REDIS_URL)

def guardar_estado(clave, valor):
    """Guardar un valor en Redis como string JSON."""
    redis_client.set(clave, valor)

def obtener_estado(clave):
    """Obtener un valor de Redis, retorna None si no existe."""
    valor = redis_client.get(clave)
    if valor:
        return valor.decode("utf-8")
    return None

def eliminar_estado(clave):
    """Eliminar un valor guardado en Redis."""
    redis_client.delete(clave)
