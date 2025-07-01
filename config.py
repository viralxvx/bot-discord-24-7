# config.py

import os

TOKEN = os.getenv("DISCORD_TOKEN")

CANAL_OBJETIVO = int(os.getenv("CANAL_OBJETIVO", "0"))
CANAL_LOGS = int(os.getenv("CANAL_LOGS", "0"))
CANAL_FALTAS = int(os.getenv("CANAL_FALTAS", "0"))
CANAL_REPORTE = int(os.getenv("CANAL_REPORTE", "0"))

MAX_LOG_LENGTH = 1900  # Puedes ajustar este valor si quieres
