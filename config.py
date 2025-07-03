import os
from dotenv import load_dotenv

load_dotenv()

def get_env_int(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"❌ Error: la variable de entorno '{var_name}' no está definida.")
    return int(value)

def get_env(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"❌ Error: la variable de entorno '{var_name}' no está definida.")
    return value

# Variables críticas convertidas en enteros
CANAL_PRESENTATE_ID = get_env_int("CANAL_PRESENTATE")
CANAL_NORMAS_ID = get_env_int("CANAL_NORMAS")
CANAL_FALTAS_ID = get_env_int("CANAL_FALTAS")
CANAL_LOGS_ID = get_env_int("CANAL_LOGS")
CANAL_COMANDOS_ID = get_env_int("CANAL_COMANDOS")
CANAL_OBJETIVO_ID = get_env_int("CANAL_OBJETIVO")
CANAL_REPORTE_ID = get_env_int("CANAL_REPORTE")
ADMIN_ID = get_env_int("ADMIN_ID")
GUILD_ID = get_env_int("GUILD_ID")

# Variables de texto
REDIS_URL = get_env("REDIS_URL")
STATE_PATH = get_env("STATE_PATH")
DISCORD_TOKEN = get_env("DISCORD_TOKEN")
