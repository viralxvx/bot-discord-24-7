# mensajes/viral_texto.py

# --- MENSAJE FIJO (para fijar como reglas en el canal) ---
TITULO_FIJO = "🧵 ¡Bienvenido a GO-VIRAL!"
IMAGEN_URL = "https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj"

DESCRIPCION_FIJO = (
    "Este es el canal donde *todos nos apoyamos* para viralizar nuestro contenido en 𝕏 (Twitter).\n\n"
    "**Lee estas reglas y síguelas al pie de la letra para participar:**\n"
    "---\n"
    "1️⃣ **Formato correcto de publicación:**\n"
    "• Solo se permite el enlace limpio de tu tweet:\n"
    "`https://x.com/usuario/status/1234567890`\n"
    "• El bot corregirá automáticamente los enlaces mal formateados, simulando que fuiste tú quien publicó.\n"
    "(Recibirás un aviso educativo de 15 segundos y un DM explicándote el error).\n\n"
    "2️⃣ **Valida tu publicación:**\n"
    "• Reacciona con 👍 a tu propio post *en los primeros 2 minutos*.\n"
    "• Si no reaccionas a tiempo, el bot eliminará tu mensaje automáticamente.\n\n"
    "3️⃣ **Apoya antes de publicar de nuevo:**\n"
    "• Debes dar **apoyo genuino** (🔥 RT + Like + Comentario) a los anteriores disponibles (**hasta 9**). "
    "Si hay menos desde tu último post, apoya a esos.\n\n"
    "4️⃣ **Intervalo entre publicaciones:**\n"
    "• Espera al menos **2 publicaciones válidas** de otros miembros antes de volver a publicar.\n"
    "• Si pasan **24h** desde tu último post y nadie publica, puedes volver a publicar.\n\n"
    "5️⃣ **Importante:**\n"
    "• No uses 🔥 en tu propio post.\n"
    "• No recicles hilos sin permiso.\n"
    "• No borres tus publicaciones después de publicarlas aquí.\n\n"
    "6️⃣ **Consecuencias y faltas:**\n"
    "• 1ª falta: Aviso por DM.\n"
    "• 2ª falta: Bloqueo 24h.\n"
    "• 3ª falta: Bloqueo 1 semana (luego reinicia el ciclo).\n"
    "• El sistema es automático y justo.\n"
    "---\n"
    "🧩 **¿Dudas o problemas?**\n"
    "• Lee las reglas completas en `#✅normas-generales`.\n"
    "• Pregunta siempre en `#👨🔧soporte` antes de molestar a los moderadores.\n\n"
    "🔥 **Aquí se viene a crecer. El que apoya, crece. El que aprende, nunca se queda atrás.**\n"
    "---\n"
    "*Mensaje automatizado por VXbot — actualizado al {fecha}*"
)

# --- MENSAJE BIENVENIDA PRIMERA PUBLICACIÓN ---
TITULO_BIENVENIDA = "🎉 ¡Bienvenido/a a tu primera publicación en GO-VIRAL!"
DESCRIPCION_BIENVENIDA = (
    "👏 Te acabas de unir al sistema de apoyo viral de la comunidad. Aquí, cada publicación cuenta y cada miembro suma.\n\n"
    "**¡Atención! En tu primera publicación, NO necesitas apoyar a nadie antes de publicar.**\n"
    "A partir de tu próxima publicación, recuerda siempre:\n"
    "• Apoyar con 🔥 (RT + LIKE + Comentario) a los anteriores disponibles (hasta 9) antes de volver a publicar. Si hay menos desde tu última publicación, solo apoya esas.\n"
    "• Reaccionar con 👍 a tus propios posts en los primeros 2 minutos.\n"
    "• Esperar que al menos 2 personas publiquen después de ti, o 24h si nadie publica, antes de volver a compartir.\n"
    "• Usa solo enlaces limpios como este:\n"
    "`https://x.com/usuario/status/1234567890`\n\n"
    "🤖 *El bot automatizará todo el proceso, te avisará si algo no está bien y te ayudará a aprender cada paso.*\n\n"
    "🔗 Si tienes dudas, lee las reglas en `#✅normas-generales` o pregunta en `#👨🔧soporte`.\n"
    "---\n"
    "¡Gracias por ser parte del crecimiento colectivo!"
)

# --------------------- NOTIFICACIONES EDUCATIVAS EMBED -----------------------

# URL
TITULO_URL_EDU = "⚠️ Enlace corregido automáticamente"
DESCRIPCION_URL_EDU = (
    "Tu enlace tenía un formato incorrecto y ha sido corregido automáticamente por el sistema.\n"
    "Asegúrate de publicar solo enlaces limpios como:\n"
    "`https://x.com/usuario/status/1234567890`\n"
    "Practica el formato correcto para evitar sanciones en el futuro."
)

TITULO_URL_DM = "📬 Enlace corregido en GO-VIRAL"
DESCRIPCION_URL_DM = (
    "Hola, {usuario}. Tu última publicación en #🧵go-viral fue corregida automáticamente "
    "porque el enlace no tenía el formato correcto. Recuerda que solo se permite el formato limpio:\n"
    "`https://x.com/usuario/status/1234567890`\n"
    "Esta vez fue solo educativo, pero la próxima vez podría considerarse una falta.\n"
    "¡Gracias por tu atención! — VXbot"
)

# LIKE
TITULO_SIN_LIKE_EDU = "❗ Publicación eliminada por no validar con 👍"
DESCRIPCION_SIN_LIKE_EDU = (
    "{usuario}, no reaccionaste con 👍 a tu propio post en los primeros 2 minutos. "
    "Por norma del canal, tu publicación fue eliminada. ¡Recuerda validar tu post la próxima vez!"
)

TITULO_SIN_LIKE_DM = "Aviso: Falta de validación en GO-VIRAL"
DESCRIPCION_SIN_LIKE_DM = (
    "Hola, tu publicación en 🧵go-viral fue eliminada porque no le diste 👍 en los primeros 2 minutos. "
    "Es necesario validar tu propio post con un 👍 para mantener el orden y la calidad. "
    "Si tienes dudas, revisa las reglas en #✅normas-generales o pregunta en #👨🔧soporte."
)

# APOYO ANTERIORES (hasta 9)
TITULO_APOYO_9_EDU = "🚨 Falta de apoyo a los anteriores disponibles"
DESCRIPCION_APOYO_9_EDU = (
    "{usuario}, antes de volver a publicar debes apoyar con 🔥 a los anteriores disponibles (hasta 9). "
    "Si hay menos, solo apoya a esas publicaciones. Por favor apoya a los demás para poder compartir tu contenido."
)

TITULO_APOYO_9_DM = "Aviso: No apoyaste a los anteriores disponibles"
DESCRIPCION_APOYO_9_DM = (
    "Hola, tu última publicación en 🧵go-viral fue eliminada porque no diste apoyo a los anteriores disponibles (hasta 9). "
    "Recuerda: solo puedes volver a publicar después de apoyar con 🔥 (RT + Like + Comentario) a esas publicaciones."
)

# INTERVALO ENTRE PUBLICACIONES
TITULO_INTERVALO_EDU = "⏳ Intervalo insuficiente entre publicaciones"
DESCRIPCION_INTERVALO_EDU = (
    "{usuario}, debes esperar al menos que **2 miembros diferentes** publiquen antes de volver a compartir, "
    "o 24h si nadie publica. ¡Apoya, espera y sigue creciendo! Publica de nuevo cuando cumplas el intervalo."
)

TITULO_INTERVALO_DM = "Aviso: No esperaste el intervalo mínimo"
DESCRIPCION_INTERVALO_DM = (
    "Hola, tu publicación fue eliminada porque no esperaste que al menos 2 miembros publicaran después de tu último post. "
    "Recuerda: después de tu publicación, deben pasar 2 publicaciones válidas de otros antes de volver a publicar. "
    "Si pasan 24h y nadie publica, puedes volver a participar."
)

# --- PERMISOS SOLO URL (NO TEXTO NI OTROS MENSAJES) ---
TITULO_SOLO_URL_EDU = "🚫 Solo se permite publicar enlaces de X (Twitter)"
DESCRIPCION_SOLO_URL_EDU = (
    "{usuario}, en este canal solo puedes publicar enlaces directos de tus publicaciones de X:\n"
    "`https://x.com/usuario/status/1234567890`\n\n"
    "Los mensajes de texto, imágenes, o cualquier otro tipo de contenido serán eliminados automáticamente.\n"
    "Por favor, comparte solo tu enlace para mantener el orden del canal.\n"
    "---\n"
    "¿Tienes dudas? Pregunta en `#👨🔧soporte`."
)

TITULO_SOLO_URL_DM = "Solo se permiten enlaces en #🧵go-viral"
DESCRIPCION_SOLO_URL_DM = (
    "Hola, tu mensaje fue eliminado de #🧵go-viral porque solo se permiten enlaces directos de publicaciones de X (Twitter), "
    "no se permiten textos, imágenes u otro contenido.\n\n"
    "Por favor, comparte únicamente el enlace de tu tweet.\n"
    "Si tienes dudas, escribe en #👨🔧soporte."
)

# --- SOLO REACCIONES PERMITIDAS (🔥 y 👍) ---
TITULO_SOLO_REACCION_EDU = "🚫 Solo se permiten reacciones 🔥 y 👍"
DESCRIPCION_SOLO_REACCION_EDU = (
    "{usuario}, en este canal solo puedes reaccionar a publicaciones con 🔥 (apoyo) o 👍 (validación).\n"
    "Las demás reacciones serán eliminadas automáticamente para mantener el orden y la claridad.\n"
    "Gracias por apoyar correctamente a la comunidad.\n"
    "---\n"
    "¿Tienes dudas? Pregunta en `#👨🔧soporte`."
)

TITULO_SOLO_REACCION_DM = "Solo 🔥 y 👍 permitidos en #🧵go-viral"
DESCRIPCION_SOLO_REACCION_DM = (
    "Hola, tu reacción ha sido eliminada en #🧵go-viral porque solo se permiten las reacciones 🔥 (apoyo) y 👍 (validación).\n"
    "Por favor, utiliza solo esas reacciones para apoyar a tus compañeros.\n"
    "Si tienes dudas, escribe en #👨🔧soporte."
)

