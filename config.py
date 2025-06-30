# config.py
import os

TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]
ADMIN_ID = os.environ.get("ADMIN_ID", "1174775323649392844")
INACTIVITY_TIMEOUT = 300
MAX_MENSAJES_RECIENTES = 10
MAX_LOG_LENGTH = 500
LOG_BATCH_DELAY = 1.0
STATE_FILE = "state.json"

# Canales constantes
CANAL_LOGS = "📝logs"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "👨🔧soporte"
CANAL_FLUJO_SOPORTE = "flujo-de-soporte"
CANAL_ANUNCIOS = "🔔anuncios"
CANAL_NORMAS_GENERALES = "✅normas-generales"
CANAL_X_NORMAS = "𝕏-normas"
CANAL_FALTAS = "📤faltas"

# Mensajes constantes
MENSAJE_NORMAS = "📌 **Bienvenid@ al canal 🧵go-viral**\n\n"  # (completo)
MENSAJE_ANUNCIO_PERMISOS = "🚨 **NUEVA REGLA: Permisos de Inactividad**\n\n"  # (completo)
MENSAJE_ACTUALIZACION_SISTEMA = "🚫 **FALTAS DE LOS USUARIOS**\n\n"  # (completo)
