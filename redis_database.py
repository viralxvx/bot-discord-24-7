import redis
import os
import json
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('redis')

# Configurar conexión a Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Claves para Redis
STATE_KEY = "discord_bot_state"

def test_connection():
    try:
        redis_conn.ping()
        logger.info("✅ Conexión a Redis establecida")
        return True
    except redis.ConnectionError as e:
        logger.error(f"❌ Error conectando a Redis: {str(e)}")
        return False

def migrate_from_json(file_path="state.json"):
    """Migrar datos desde state.json a Redis"""
    try:
        with open(file_path, "r") as f:
            state = json.load(f)
            redis_conn.set(STATE_KEY, json.dumps(state))
            logger.info("✅ Datos migrados a Redis desde state.json")
            return True
    except FileNotFoundError:
        logger.warning("⚠️ state.json no encontrado, iniciando con Redis vacío")
        return False
    except json.JSONDecodeError:
        logger.error("❌ Error decodificando state.json")
        return False

def load_state():
    """Cargar estado desde Redis"""
    state_json = redis_conn.get(STATE_KEY)
    if state_json:
        try:
            return json.loads(state_json)
        except json.JSONDecodeError:
            logger.error("❌ Error decodificando datos de Redis")
            return {}
    
    # Intentar migrar si no hay datos en Redis
    if migrate_from_json():
        return load_state()
    
    return {}

def save_state(state):
    """Guardar estado en Redis"""
    try:
        redis_conn.set(STATE_KEY, json.dumps(state))
        return True
    except Exception as e:
        logger.error(f"❌ Error guardando en Redis: {str(e)}")
        return False

# Probar conexión al importar
test_connection()
