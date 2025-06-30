# Nombre de canales utilizados
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "🆘soporte"
CANAL_FALTAS = "📤faltas"
CANAL_OBJETIVO = "🧵go-viral"
CANAL_LOGS = "📝logs"
CANAL_PRESENTATE = "👉preséntate"
CANAL_ANUNCIOS = "📢anuncios"
CANAL_NORMAS_GENERALES = "📚normas-generales"
CANAL_X_NORMAS = "📜x-normas"

# Token y IDs sensibles (asegúrate de usar variables de entorno en producción)
import os
TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_ID = os.getenv("DISCORD_ADMIN_ID", "123456789012345678")  # ID por defecto si no se define

# Mensajes predeterminados
MENSAJE_NORMAS = (
    "📜 **Normas Generales del Canal**:\n\n"
    "1. Publica un solo enlace por día y en el formato correcto (solo un link de X).\n"
    "2. Reacciona con 🔥 a los posts publicados después del tuyo (mínimo 1).\n"
    "3. Dale 👍 a tu propio post tras publicarlo.\n"
    "4. No repitas mensajes ni spammees.\n\n"
    "❗El incumplimiento resultará en advertencias o baneo temporal."
)

MENSAJE_ANUNCIO_PERMISOS = (
    "📢 **Recuerda**: si no puedes participar temporalmente, escribe `!permiso <días>` en "
    f"#{CANAL_REPORTES} (máximo 7 días).\n"
    "⛔ Si acumulas 3 faltas por inactividad, serás baneado automáticamente."
)

# Fallback para preguntas frecuentes
FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": (
        "VX es una comunidad que te ayuda a hacer viral tu contenido en X.\n"
        "Publicas tu tweet y apoyas a otros con 🔥 y 👍.\n"
        "¡El trabajo en equipo da resultados!"
    ),
    "✅ ¿Cómo publico mi post?": (
        "Solo publica tu enlace de X en #🧵go-viral, sin texto adicional ni emojis.\n"
        "Debes dar 🔥 a al menos 1 post antes de publicar el tuyo.\n"
        "Reacciona a tu propio post con 👍 tras publicarlo."
    ),
    "✅ ¿Cómo subo de nivel?": (
        "Apoya a otros, cumple las normas, y mantente activo.\n"
        "Los miembros con buen historial reciben reconocimiento y acceso a funciones exclusivas."
    ),
}
