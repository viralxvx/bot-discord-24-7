import os

TOKEN = os.getenv("DISCORD_TOKEN", "tu_token_aqui")

PREFIX = "!"

ADMIN_ID = os.getenv("ADMIN_ID", "123456789012345678")  # Cambia por el ID real del admin

CANAL_OBJETIVO = "🧵go-viral"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "🔧soporte-técnico"
CANAL_FALTAS = "📤faltas"
CANAL_LOGS = "📝logs"
CANAL_NORMAS_GENERALES = "📜normas-generales"
CANAL_ANUNCIOS = "📢anuncios"
CANAL_X_NORMAS = "❌x-normas"

MAX_MENSAJES_RECIENTES = 10
INACTIVITY_TIMEOUT = 3600  # segundos para limpiar conversaciones activas (1 hora)

# Mensajes fijos que se usan en varios módulos
MENSAJE_NORMAS = (
    "📜 **Normas de la comunidad:**\n"
    "- No spam\n"
    "- Respeto entre usuarios\n"
    "- Formato correcto en publicaciones\n"
    "- Sigue las instrucciones de los moderadores\n"
)

MENSAJE_ANUNCIO_PERMISOS = (
    "📢 Recuerda usar `!permiso <días>` para solicitar permisos de inactividad (máx. 7 días)."
)
