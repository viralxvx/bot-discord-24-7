# config.py
TOKEN = "your_bot_token_here"  # Configurado en las variables de entorno en Railway
CANAL_OBJETIVO = "go-viral"  # Ajusta según el nombre exacto en Discord
CANAL_FALTAS = "faltas"  # Ajusta según el nombre exacto (por ejemplo, "📤faltas" o "faltas")
CANAL_REPORTES = "reporte-de-incumplimiento"  # Ajusta según el nombre exacto
CANAL_SOPORTE = "soporte"  # Ajusta según el nombre exacto
CANAL_NORMAS_GENERALES = "✅normas-generales"  # Coincide con el canal en los logs
CANAL_ANUNCIOS = "anuncios"  # Ajusta según el nombre exacto
CANAL_LOGS = "logs"  # Ajusta según el nombre exacto
CANAL_FLUJO_SOPORTE = "soporte"  # Ajusta si es diferente
MAX_LOG_LENGTH = 2000  # Longitud máxima para los mensajes de log en Discord
LOG_BATCH_DELAY = 60  # Segundos entre envíos de lotes de logs
INACTIVITY_TIMEOUT = 7  # Días de inactividad antes de registrar una falta

MENSAJE_NORMAS = (
    "📜 **Normas Generales**\n\n"
    "1. Publica contenido relevante en #go-viral.\n"
    "2. Respeta a los demás miembros.\n"
    "3. Usa `!permiso <días>` para solicitar inactividad."
)
MENSAJE_ANUNCIO_PERMISOS = (
    "📢 **Anuncio sobre Permisos**\n\n"
    "Recuerda usar `!permiso <días>` en #reporte-de-incumplimiento para pausar la obligación de publicar."
)
MENSAJE_ACTUALIZACION_SISTEMA = (
    "🚫 **FALTAS DE LOS USUARIOS**\n\n"
    "Aquí se muestra el estado de las faltas de los usuarios."
)
FAQ_FALLBACK = {
    "¿Cómo reporto una infracción?": "Menciona al usuario en #reporte-de-incumplimiento y selecciona la infracción.",
    "¿Cómo solicito un permiso?": "Usa `!permiso <días>` en #reporte-de-incumplimiento."
}
STATE_FILE = "/data/state.json"
