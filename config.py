import os

# Token del bot Discord (asegúrate de definir DISCORD_TOKEN en Railway)
TOKEN = os.getenv("DISCORD_TOKEN")

# Prefijo para comandos
PREFIX = "!"

# ID del administrador (opcional, define ADMIN_ID en Railway, si no 0)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Nombres de canales usados en el bot
CANAL_SOPORTE = "👨🔧soporte"
CANAL_LOGS = "📜logs"
CANAL_FALTAS = "📤faltas"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_OBJETIVO = "🧵go-viral"
CANAL_NORMAS_GENERALES = "✅normas-generales"
CANAL_X_NORMAS = "𝕏-normas"
CANAL_ANUNCIOS = "🔔anuncios"

# Máximo mensajes recientes para control antispam
MAX_MENSAJES_RECIENTES = 10

# Mensajes de fallback (ejemplo)
FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": "Aquí va la respuesta por defecto para VX.",
    "✅ ¿Cómo publico mi post?": "Aquí va la respuesta para publicar post.",
    "✅ ¿Cómo subo de nivel?": "Aquí va la respuesta para subir de nivel."
}

# Mensaje normas ejemplo
MENSAJE_NORMAS = (
    "Por favor, sigue las normas del servidor para evitar sanciones."
)

# Otros parámetros globales que uses pueden ir aquí...
