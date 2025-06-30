import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Claves de Redis
CLAVES = {
    "faltas_dict": "vx:faltas_dict",
    "amonestaciones": "vx:amonestaciones",
    "ultima_publicacion": "vx:ultima_publicacion",
    "permisos_inactividad": "vx:permisos_inactividad",
    "baneos_temporales": "vx:baneos_temporales",
    "mensajes_recientes": "vx:mensajes_recientes",
    "active_conversations": "vx:active_conversations"
}

# Cargar estado
def cargar_estado():
    return {
        "faltas_dict": json.loads(redis_client.get(CLAVES["faltas_dict"]) or "{}"),
        "amonestaciones": json.loads(redis_client.get(CLAVES["amonestaciones"]) or "{}"),
        "ultima_publicacion_dict": json.loads(redis_client.get(CLAVES["ultima_publicacion"]) or "{}"),
        "permisos_inactividad": json.loads(redis_client.get(CLAVES["permisos_inactividad"]) or "{}"),
        "baneos_temporales": json.loads(redis_client.get(CLAVES["baneos_temporales"]) or "{}"),
        "mensajes_recientes": json.loads(redis_client.get(CLAVES["mensajes_recientes"]) or "{}"),
        "active_conversations": json.loads(redis_client.get(CLAVES["active_conversations"]) or "{}"),
    }

# Guardar estado
def guardar_estado(
    faltas_dict,
    amonestaciones,
    ultima_publicacion_dict,
    permisos_inactividad,
    baneos_temporales,
    mensajes_recientes,
    active_conversations
):
    redis_client.set(CLAVES["faltas_dict"], json.dumps(faltas_dict))
    redis_client.set(CLAVES["amonestaciones"], json.dumps(amonestaciones))
    redis_client.set(CLAVES["ultima_publicacion"], json.dumps(ultima_publicacion_dict))
    redis_client.set(CLAVES["permisos_inactividad"], json.dumps(permisos_inactividad))
    redis_client.set(CLAVES["baneos_temporales"], json.dumps(baneos_temporales))
    redis_client.set(CLAVES["mensajes_recientes"], json.dumps(mensajes_recientes))
    redis_client.set(CLAVES["active_conversations"], json.dumps(active_conversations))
