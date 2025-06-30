import redis
import os
import json
from typing import Any

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

r = redis.from_url(REDIS_URL, decode_responses=True)

def save_state(key: str, data: Any):
    """Guarda datos en Redis en formato JSON."""
    try:
        json_data = json.dumps(data)
        r.set(key, json_data)
    except Exception as e:
        print(f"Error guardando estado en Redis: {e}")

def load_state(key: str, default=None):
    """Carga datos desde Redis, parseando JSON."""
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
        return default
    except Exception as e:
        print(f"Error cargando estado de Redis: {e}")
        return default
