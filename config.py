import os
from dotenv import load_dotenv

load_dotenv()

# IDs de canales (se cargan desde variables de entorno)
CANAL_PRESENTATE_ID = int(os.getenv("CANAL_PRESENTATE"))
CANAL_NORMAS_ID = int(os.getenv("CANAL_NORMAS"))
CANAL_FALTAS_ID = int(os.getenv("CANAL_FALTAS"))
CANAL_LOGS_ID = int(os.getenv("CANAL_LOGS"))
CANAL_COMANDOS_ID = int(os.getenv("CANAL_COMANDOS"))
CANAL_OBJETIVO_ID = int(os.getenv("CANAL_OBJETIVO"))
CANAL_REPORTE_ID = int(os.getenv("CANAL_REPORTE"))

# Otros datos
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))
REDIS_URL = os.getenv("REDIS_URL")
STATE_PATH = os.getenv("STATE_PATH")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
