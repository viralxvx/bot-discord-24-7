# config.py

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
ASISTENTE_API_URL = get_env_variable("ASISTENTE_API_URL")
ADMIN_ID = int(get_env_variable("ADMIN_ID"))
ADMIN_ROLE_ID = int(get_env_variable("ADMIN_ROLE_ID"))  # ✅ Para comando /ver_testimonios
CANAL_TESTIMONIOS_ID = int(get_env_variable("CANAL_TESTIMONIOS"))  # ✅ Canal oficial de testimonios

# IDs de canales principales
CANAL_PRESENTATE_ID      = int(get_env_variable("CANAL_PRESENTATE"))
CANAL_NORMAS_ID          = int(get_env_variable("CANAL_NORMAS"))
CANAL_OBJETIVO_ID        = int(get_env_variable("CANAL_OBJETIVO"))      # 🧵go-viral
CANAL_FALTAS_ID          = int(get_env_variable("CANAL_FALTAS"))
CANAL_LOGS_ID            = int(get_env_variable("CANAL_LOGS"))          # 📝logs
CANAL_REPORTE_ID         = int(get_env_variable("CANAL_REPORTE"))       # ⛔reporte-incumplimiento
CANAL_COMANDOS_ID        = int(get_env_variable("CANAL_COMANDOS"))

# Alias para compatibilidad premium
CANAL_ANUNCIOS = int(get_env_variable("CANAL_ANUNCIOS"))
CANAL_FUNCIONES = int(get_env_variable("CANAL_FUNCIONES"))

# IDs de canales de menú/bienvenida
CANAL_GUIAS_ID           = int(get_env_variable("CANAL_GUIAS"))
CANAL_NORMAS_GENERALES_ID= int(get_env_variable("CANAL_NORMAS"))        # Alias para claridad
CANAL_VICTORIAS_ID       = int(get_env_variable("CANAL_VICTORIAS"))
CANAL_ESTRATEGIAS_ID     = int(get_env_variable("CANAL_ESTRATEGIAS"))
CANAL_ENTRENAMIENTO_ID   = int(get_env_variable("CANAL_ENTRENAMIENTO"))
CANAL_SOPORTE_ID         = int(get_env_variable("CANAL_SOPORTE"))
CANAL_GPT_ID             = int(get_env_variable("CANAL_GPT"))           # Canal GPT

# Emojis permitidos en el canal 🧵go-viral
EMOJIS_PERMITIDOS = ["🔥", "👍"]

# ✅ NUEVA FUNCIÓN PARA MÓDULOS QUE USAN get_env_int()
def get_env_int(name):
    return int(get_env_variable(name))
