# mensajes/viral_texto.py

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
    "• Debes dar **apoyo genuino** (🔥 RT + Like + Comentario) a los **9 compañeros anteriores** antes de volver a publicar.\n"
    "• Si hay menos de 9 publicaciones, apoya a todas las disponibles.\n\n"
    "4️⃣ **Intervalo entre publicaciones:**\n"
    "• Espera al menos **2 publicaciones válidas** de otros miembros antes de volver a publicar.\n"
    "• Si solo hay 2 publicaciones después de la tuya (y ya las apoyaste), puedes volver a publicar aunque haya pasado 1 día.\n\n"
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

TITULO_BIENVENIDA = "🎉 ¡Bienvenido/a a tu primera publicación en GO-VIRAL!"
DESCRIPCION_BIENVENIDA = (
    "👏 Te acabas de unir al sistema de apoyo viral de la comunidad. Aquí, cada publicación cuenta y cada miembro suma.\n\n"
    "**¿Qué debes saber a partir de ahora?**\n"
    "• Recuerda apoyar con 🔥 (RT + LIKE + Comentario) a los 9 compañeros anteriores antes de tu próxima publicación.\n"
    "• Siempre reacciona con 👍 a tus propios posts en los primeros 2 minutos.\n"
    "• Entre cada publicación tuya, espera que al menos 2 personas publiquen después.\n"
    "• Usa solo enlaces limpios como este:\n"
    "`https://x.com/usuario/status/1234567890`\n\n"
    "🤖 *El bot automatizará todo el proceso, te avisará si algo no está bien y te ayudará a aprender cada paso.*\n\n"
    "🔗 Si tienes dudas, lee las reglas en `#✅normas-generales` o pregunta en `#👨🔧soporte`.\n"
    "---\n"
    "¡Gracias por ser parte del crecimiento colectivo!"
)

# ---------- NOTIFICACIONES EDUCATIVAS EMBED ----------

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

TITULO_APOYO_9_EDU = "🚨 Falta de apoyo a los 9 anteriores"
DESCRIPCION_APOYO_9_EDU = (
    "{usuario}, antes de volver a publicar debes apoyar con 🔥 a los 9 compañeros anteriores. "
    "Por favor apoya a los demás para poder compartir tu contenido."
)

TITULO_APOYO_9_DM = "Aviso: No apoyaste a los 9 anteriores"
DESCRIPCION_APOYO_9_DM = (
    "Hola, tu última publicación en 🧵go-viral fue eliminada porque no diste apoyo a los 9 anteriores. "
    "Recuerda: solo puedes volver a publicar después de apoyar con 🔥 (RT + Like + Comentario) a los 9 anteriores."
)

TITULO_INTERVALO_EDU = "⏳ Intervalo insuficiente entre publicaciones"
DESCRIPCION_INTERVALO_EDU = (
    "{usuario}, debes esperar al menos que **2 miembros diferentes** publiquen antes de volver a compartir. "
    "¡Apoya, espera y sigue creciendo! Publica de nuevo cuando cumplas el intervalo."
)

TITULO_INTERVALO_DM = "Aviso: No esperaste el intervalo mínimo"
DESCRIPCION_INTERVALO_DM = (
    "Hola, tu publicación fue eliminada porque no esperaste que al menos 2 miembros publicaran después de tu último post. "
    "Recuerda: después de tu publicación, deben pasar 2 publicaciones válidas de otros antes de volver a publicar."
)
