import os

TOKEN = os.getenv("DISCORD_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
CANAL_OBJETIVO = int(os.getenv("CANAL_OBJETIVO", 0))
CANAL_FALTAS = int(os.getenv("CANAL_FALTAS", 0))
CANAL_LOGS = int(os.getenv("CANAL_LOGS", 0))
