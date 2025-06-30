import discord
import os
from dotenv import load_dotenv

load_dotenv()

# TOKEN y ADMIN
TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "123456789012345678")  # reemplaza por tu ID real si deseas

# INTENTS
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
INTENTS.guilds = True
INTENTS.messages = True
INTENTS.reactions = True

# Nombres de canales
CANAL_OBJETIVO = "🧵go-viral"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "📩soporte"
CANAL_NORMAS_GENERALES = "📘normas-generales"
CANAL_ANUNCIOS = "📣anuncios"
CANAL_FALTAS = "📤faltas"
CANAL_LOGS = "📝logs"
CANAL_X_NORMAS = "📘x-normas"
CANAL_PRESENTATE = "👉preséntate"

# Mensajes fijos
MENSAJE_NORMAS = (
    "📘 **NORMAS GENERALES VX**\n\n"
    "✅ Publicar un solo tweet al día (formato correcto)\n"
    "🔥 Reaccionar a los post de otros\n"
    "👍 Dale like a tu publicación\n"
    "⚠️ No repetir mensajes\n"
    "⏳ Usa `!permiso <días>` si no puedes publicar"
)

MENSAJE_ANUNCIO_PERMISOS = (
    "🚨 **Recuerda usar `!permiso <días>` en caso de inactividad.**\n"
    "Puedes pedir hasta 7 días en #⛔reporte-de-incumplimiento"
)

# FAQ
FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": "En VX se publica 1 post diario en #🧵go-viral y debes apoyar los demás posts (🔥).",
    "✅ ¿Cómo publico mi post?": "Copia el enlace de tu tweet y pégalo en #🧵go-viral. Solo debe ser el URL, sin texto adicional.",
    "✅ ¿Cómo subo de nivel?": "Sigue las normas, apoya a otros y mantente activo para ganar reputación."
}

# Reacción y tiempo
MAX_MENSAJES_RECIENTES = 20
INACTIVITY_TIMEOUT = 1800  # 30 minutos
