import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
CANAL_OBJETIVO = int(os.getenv("CANAL_OBJETIVO"))
CANAL_FALTAS = int(os.getenv("CANAL_FALTAS"))
CANAL_LOGS = int(os.getenv("CANAL_LOGS"))
CANAL_REPORTE = int(os.getenv("CANAL_REPORTE"))
