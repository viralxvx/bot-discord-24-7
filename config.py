import os
from dotenv import load_dotenv

load_dotenv()

# Token del bot Discord (se usa en main.py)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# IDs y nombres de canales (ajusta según tu servidor)
CANAL_LOGS = "logs"                  # Nombre canal logs
CANAL_FALTAS = "faltas"              # Nombre canal faltas
CANAL_REPORTES = "reportes"          # Nombre canal reportes
CANAL_SOPORTE = "soporte"            # Nombre canal soporte
CANAL_OBJETIVO = "go-viral"          # Nombre canal objetivo (viral)
CANAL_NORMAS_GENERALES = "normas-generales"  # Nombre canal normas generales
CANAL_X_NORMAS = "x-normas"          # Nombre canal X normas
CANAL_ANUNCIOS = "anuncios"          # Nombre canal anuncios

# ID del administrador para enviar mensajes directos
ADMIN_ID = os.getenv("ADMIN_ID")

# Prefijo para comandos
COMMAND_PREFIX = "!"

# Parámetros generales
MAX_MENSAJES_RECIENTES = 5  # Número máximo de mensajes recientes para filtrado

# Mensajes predefinidos
MENSAJE_NORMAS = (
    "📜 Por favor, lee las normas del servidor y cumple con ellas para evitar sanciones."
)

# Respuestas FAQ (puedes agregar más)
FAQ_DATA = {
    "✅ ¿Cómo funciona VX?": "VX funciona así...",
    "✅ ¿Cómo publico mi post?": "Para publicar un post...",
    "✅ ¿Cómo subo de nivel?": "Para subir de nivel debes...",
}

FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": "No se encontró respuesta para esta pregunta.",
    "✅ ¿Cómo publico mi post?": "No se encontró respuesta para esta pregunta.",
    "✅ ¿Cómo subo de nivel?": "No se encontró respuesta para esta pregunta.",
}

# Aquí más configuraciones que necesites

