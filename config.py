import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))
CANAL_FALTAS = int(os.getenv("CANAL_FALTAS"))
CANAL_LOGS = int(os.getenv("CANAL_LOGS"))
CANAL_OBJETIVO = int(os.getenv("CANAL_OBJETIVO"))
CANAL_REPORTE = int(os.getenv("CANAL_REPORTE"))
CANAL_COMANDOS = int(os.getenv("CANAL_COMANDOS"))

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
REDIS_URL = os.getenv("REDIS_URL")
STATE_PATH = os.getenv("STATE_PATH", "./state.json")
