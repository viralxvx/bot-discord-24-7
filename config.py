import os

TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ.get("CANAL_OBJETIVO", "🧵go-viral")
ADMIN_ID = os.environ.get("ADMIN_ID", "1174775323649392844")
INACTIVITY_TIMEOUT = 300
MAX_MENSAJES_RECIENTES = 10
MAX_LOG_LENGTH = 500
LOG_BATCH_DELAY = 1.0

CANAL_LOGS = "📝logs"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "👨🔧soporte"
CANAL_FLUJO_SOPORTE = "flujo-de-soporte"
CANAL_ANUNCIOS = "🔔anuncios"
CANAL_NORMAS_GENERALES = "✅normas-generales"
CANAL_X_NORMAS = "𝕏-normas"
CANAL_FALTAS = "📤faltas"

MENSAJE_NORMAS = (
    "📌 **Bienvenid@ al canal 🧵go-viral**\n\n"
    "🔹 **Reacciona con 🔥** a todas las publicaciones de otros miembros desde tu última publicación antes de volver a publicar.\n"
    "🔹 **Reacciona con 👍** a tu propia publicación.\n"
    "🔹 **Solo se permiten enlaces de X (Twitter)** con este formato:\n"
    "```https://x.com/usuario/status/1234567890123456789```\n"
    "❌ **Publicaciones con texto adicional, formato incorrecto o repetidas** serán eliminadas y contarán como una falta, reduciendo tu calificación en 1%.\n"
    "⏳ **Permisos de inactividad**: Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para pausar la obligación de publicar hasta 7 días. Extiende antes de que expire.\n"
    "🚫 **Mensajes repetidos** serán eliminados en todos los canales (excepto #📝logs) para mantener el servidor limpio."
)

MENSAJE_ANUNCIO_PERMISOS = (
    "🚨 **NUEVA REGLA: Permisos de Inactividad**\n\n"
    "**Ahora puedes solicitar un permiso de inactividad** en #⛔reporte-de-incumplimiento usando el comando `!permiso <días>`:\n"
    "✅ **Máximo 7 días** por permiso.\n"
    "🔄 **Extiende el permiso** con otro reporte antes de que expire, siempre antes de un baneo.\n"
    "📤 **Revisa tu estado** en #📤faltas para mantenerte al día.\n"
    "🚫 **Mensajes repetidos** serán eliminados en todos los canales (excepto #📝logs) para mantener el servidor limpio.\n"
    "¡**Gracias por mantener la comunidad activa y organizada**! 🚀"
)

MENSAJE_ACTUALIZACION_SISTEMA = (
    "🚫 **FALTAS DE LOS USUARIOS**\n\n"
    "**Reglas de Inactividad**:\n"
    "⚠️ Si un usuario pasa **3 días sin publicar** en #🧵go-viral, será **baneado por 7 días** de forma automática.\n"
    "⛔️ Si después del baneo pasa **otros 3 días sin publicar**, el sistema lo **expulsará automáticamente** del servidor.\n\n"
    "**Permisos de Inactividad**:\n"
    "✅ Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para solicitar un permiso de hasta **7 días**.\n"
    "🔄 Puedes **extender el permiso** antes de que expire, siempre antes de un baneo.\n"
    "✅ Estas medidas buscan mantener una **comunidad activa y comprometida**, haciendo que el programa de crecimiento sea más eficiente.\n"
    "📤 **Revisa tu estado** en este canal (#📤faltas) para mantenerte al día con tu participación.\n\n"
    "**Gracias por tu comprensión y compromiso. ¡Sigamos creciendo juntos!** 🚀"
)

FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": "VX es una comunidad donde crecemos apoyándonos. Tú apoyas, y luego te apoyan. Publicas tu post después de apoyar a los demás. 🔥 = apoyaste, 👍 = tu propio post.",
    "✅ ¿Cómo publico mi post?": "Para publicar: 1️⃣ Apoya todos los posts anteriores (like + RT + comentario) 2️⃣ Reacciona con 🔥 en Discord 3️⃣ Luego publica tu post y colócale 👍. No uses 🔥 en tu propio post ni repitas mensajes.",
    "✅ ¿Cómo subo de nivel?": "Subes de nivel participando activamente, apoyando a todos y siendo constante. Los niveles traen beneficios como prioridad, mentoría y más."
}
