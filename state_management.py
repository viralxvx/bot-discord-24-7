import asyncio
import json
from redis_database import redis_client

# Prefijos para las keys en Redis
ACTIVE_CONV_KEY = "active_conversations"
FALTAS_DICT_KEY = "faltas_dict"
ULTIMA_PUBLICACION_KEY = "ultima_publicacion_dict"

async def save_state(key: str, data: dict):
    """Guarda el estado serializado en Redis"""
    try:
        await redis_client.set(key, json.dumps(data))
    except Exception as e:
        print(f"Error guardando estado {key}: {e}")

async def load_state(key: str) -> dict:
    """Carga el estado desde Redis, o devuelve dict vacío si no existe"""
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return {}
    except Exception as e:
        print(f"Error cargando estado {key}: {e}")
        return {}

# Funciones específicas para cada estado

async def save_active_conversations(state: dict):
    await save_state(ACTIVE_CONV_KEY, state)

async def load_active_conversations() -> dict:
    return await load_state(ACTIVE_CONV_KEY)

async def save_faltas_dict(state: dict):
    await save_state(FALTAS_DICT_KEY, state)

async def load_faltas_dict() -> dict:
    return await load_state(FALTAS_DICT_KEY)

async def save_ultima_publicacion_dict(state: dict):
    await save_state(ULTIMA_PUBLICACION_KEY, state)

async def load_ultima_publicacion_dict() -> dict:
    return await load_state(ULTIMA_PUBLICACION_KEY)
