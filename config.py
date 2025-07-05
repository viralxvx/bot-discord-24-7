import os
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name):
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"❌ Error: la variable de entorno '{name}' no está definida.")
    return value

# Variables principales
DISCORD_TOKEN = get_env_variable("DISCORD_TOKEN")
GUILD_ID = int(get_env_variable("GUILD_ID"))
REDIS_URL = get_env_variable("REDIS_URL")
STATE_PATH = get_env_variable("STATE_PATH")
ADMIN_ID = int(get_env_variable("ADMIN_ID"))

# IDs de canales principales
CANAL_PRESENTATE_ID      = int(get_env_variable("CANAL_PRESENTATE"))
CANAL_NORMAS_ID          = int(get_env_variable("CANAL_NORMAS"))
CANAL_OBJETIVO_ID        = int(get_env_variable("CANAL_OBJETIVO"))      # 🧵go-viral
CANAL_FALTAS_ID          = int(get_env_variable("CANAL_FALTAS"))
CANAL_LOGS_ID            = int(get_env_variable("CANAL_LOGS"))          # 📝logs
CANAL_REPORTE_ID         = int(get_env_variable("CANAL_REPORTE"))       # ⛔reporte-incumplimiento
CANAL_COMANDOS_ID        = int(get_env_variable("CANAL_COMANDOS"))

# IDs de canales de menú/bienvenida
CANAL_GUIAS_ID           = int(get_env_variable("CANAL_GUIAS"))
CANAL_NORMAS_GENERALES_ID= int(get_env_variable("CANAL_NORMAS"))        # (Alias, para claridad)
CANAL_VICTORIAS_ID       = int(get_env_variable("CANAL_VICTORIAS"))
CANAL_ESTRATEGIAS_ID     = int(get_env_variable("CANAL_ESTRATEGIAS"))
CANAL_ENTRENAMIENTO_ID   = int(get_env_variable("CANAL_ENTRENAMIENTO"))
CANAL_SOPORTE_ID         = int(get_env_variable("CANAL_SOPORTE"))
