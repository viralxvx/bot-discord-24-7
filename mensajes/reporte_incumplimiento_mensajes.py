"""
==========================================================================
 Archivo: mensajes/reporte_incumplimiento_mensajes.py
 Autor:    Viral X | VXbot (Miguel Peralta & ChatGPT)
 Creado:   2025-07
--------------------------------------------------------------------------
 PROPÓSITO:
 Centraliza **todos los textos, embeds, plantillas de mensajes y notificaciones**
 utilizados por el sistema de reporte de incumplimiento automático.
 Esto incluye mensajes de advertencia, botones, paneles, logs, DMs, etc.

 NO MODIFICAR LA LÓGICA DEL BOT AQUÍ.
 Aquí solo se cambian textos, títulos, descripciones, frases y respuestas.
 Si quieres ajustar la lógica, hazlo en canales/reporte_incumplimiento.py

 Esto permite actualizar, personalizar o traducir el sistema fácilmente,
 sin riesgo de romper el funcionamiento del bot.

--------------------------------------------------------------------------
 PARA DESARROLLADORES:
 - Todos los textos están en variables descriptivas y agrupadas por contexto.
 - Puedes añadir variables de formato ({usuario}, {reporte_id}, etc.)
 - Los emojis se pueden cambiar aquí para estandarizar el branding del bot.
 - Los logs importantes y mensajes para consola también pueden centralizarse aquí.

--------------------------------------------------------------------------

 EJEMPLO DE USO:
 from mensajes.reporte_incumplimiento_mensajes import AVISO_ADVERTENCIA, DM_APELACION_STAFF
 await usuario.send(AVISO_ADVERTENCIA.format(usuario=usuario.mention, reporte_id=1234))
==========================================================================

"""

# ------------------------
# TEXTOS PARA USUARIOS
# ------------------------

TITULO_PANEL_INSTRUCCIONES = "🚨 Reporte de Incumplimiento"
DESCRIPCION_PANEL_INSTRUCCIONES = (
    "**¿Notas que alguien NO apoyó en X como indican las reglas?**\n\n"
    "• Usa el menú para elegir el motivo del reporte.\n"
    "• Completa los pasos y confirma.\n"
    "• Solo puedes reportar usuarios del servidor.\n\n"
    "**Motivos válidos:**\n"
    "🔸 No apoyó en X (no dio RT, Like o Comentario)\n"
    "🔸 Otro (explica brevemente)\n\n"
    "El proceso es **privado**. Ambas partes serán notificadas por DM y el caso tendrá seguimiento automático.\n"
    "*El abuso de reportes puede ser sancionado.*"
)
FOOTER_GENERAL = "VXbot | Sistema automatizado de reportes"

# ------------
# CICLO DE REPORTES
# ------------

AVISO_ADVERTENCIA = (
    "🚨 **Advertencia oficial**\n"
    "Hemos recibido un reporte indicando que **no apoyaste correctamente** a un compañero en X.\n\n"
    "Por favor, regulariza tu situación antes de avanzar a sanciones. "
    "Haz clic en el botón cuando hayas cumplido. Tienes 6 horas para evitar una sanción."
)
AVISO_RECORDATORIO = (
    "⏰ **Segundo recordatorio**\n"
    "Sigue pendiente un reporte de que no has cumplido el apoyo requerido en X.\n"
    "Esta es la segunda advertencia automática. Si no cumples, podrías ser sancionado."
)
AVISO_ULTIMA_ADVERTENCIA = (
    "🚨 **Última advertencia**\n"
    "No has regularizado tu apoyo en X tras varias oportunidades. Si no cumples en las próximas 6 horas, "
    "serás **baneado temporalmente** y podrías ser expulsado en caso de reincidencia."
)

BANEO_TEMPORAL = (
    "⛔ **Has sido baneado temporalmente (24h)** por no cumplir el apoyo requerido en X tras varias advertencias.\n"
    "Puedes regularizar tu situación al volver para evitar sanciones más graves."
)
EXPULSION_FINAL = (
    "🚫 **Has sido expulsado del servidor** por incumplir reiteradamente las normas de apoyo. "
    "Puedes apelar contactando a un administrador."
)

# -----------------------
# CONFIRMACIONES Y CICLO POSITIVO
# -----------------------

INSTRUCCION_REPORTADO_BOTON = "He apoyado / regularicé mi apoyo"
INSTRUCCION_REPORTANTE_BOTON = "Confirmo que me apoyó"
INSTRUCCION_REPORTANTE_BOTON_NO = "Aún no he sido apoyado"
INSTRUCCION_REPORTANTE_BOTON_CERRAR = "Cerrar reporte"

AVISO_REGULARIZADO_REPORTANTE = (
    "🤝 **El usuario {reportado} indicó que ya te apoyó.**\n"
    "Por favor, revisa y confirma si es cierto utilizando los botones de abajo."
)
AVISO_CIERRE_AUTOMATICO = (
    "✅ **Reporte cerrado automáticamente.**\n"
    "El apoyo fue confirmado correctamente. ¡Gracias por contribuir al orden de la comunidad!"
)
AVISO_CIERRE_MANUAL_STAFF = (
    "🔒 **El staff ha cerrado este reporte.**\n"
    "El caso se ha dado por resuelto tras su intervención."
)

AVISO_NO_RESPUESTA = (
    "❗ No hemos recibido respuesta. El proceso continuará automáticamente según las reglas."
)

# -------------------------
# MULTI-REPORTES Y AGRUPACIÓN
# -------------------------

AVISO_MULTI_REPORTADO = (
    "⚠️ **Has recibido varios reportes por no apoyar a diferentes miembros en X.**\n"
    "Debes regularizar tu apoyo con todos los reportantes. El proceso solo se cierra cuando todos confirmen."
)
AVISO_MULTI_REPORTANTE = (
    "🔔 Este usuario ya está siendo reportado por otros miembros. "
    "Te avisaremos en cuanto regularice el apoyo contigo."
)
AVISO_CIERRE_MULTI = (
    "✅ **Todos los reportantes han confirmado el apoyo. El caso ha sido cerrado automáticamente.**"
)

# ----------------------------
# DM Y RESPUESTAS DE BOTONES
# ----------------------------

DM_REPORTE_CREADO = (
    "📝 **Tu reporte ha sido abierto.**\n"
    "Te avisaremos de cada avance. Cuando el usuario regularice el apoyo, podrás validarlo aquí."
)
DM_BOTON_CONFIRMAR = "Confirmar que me apoyó"
DM_BOTON_NO_CONFIRMAR = "Aún no he sido apoyado"

DM_AVISO_REGULARIZADO = (
    "✅ **El usuario reportado indicó que ya apoyó tu publicación.**\n"
    "Por favor, confirma si es cierto. Si no, pulsa 'Aún no he sido apoyado'."
)
DM_CASO_CERRADO = (
    "🟢 **Reporte cerrado exitosamente.**\n"
    "Ambas partes han sido notificadas y el historial se ha actualizado."
)

# ----------------------------
# APELACIÓN Y STAFF
# ----------------------------

BOTON_APELAR = "📝 Apelar reporte"
AVISO_APELACION_CONFIRM = (
    "📝 Tu apelación ha sido recibida. Un administrador revisará tu caso y te contactará por DM."
)
DM_APELACION_STAFF = (
    "📢 El usuario {usuario} ha solicitado una **apelación** al reporte #{reporte_id}.\n"
    "Revisa el caso y responde manualmente desde el panel."
)
AVISO_STAFF_PERDONADO = (
    "🔔 **El staff ha decidido perdonar la sanción en tu reporte #{reporte_id}.**\n"
    "El caso queda cerrado y tu historial actualizado."
)
AVISO_STAFF_FORZADO = (
    "⚠️ **El staff ha forzado el cierre del reporte #{reporte_id}.**"
)

# ----------------------------
# LOGS Y CONSOLA
# ----------------------------

LOG_REPORTE_CREADO = "🔎 Reporte #{reporte_id} creado por {reportante} contra {reportado}"
LOG_REPORTE_CERRADO_AUTO = "✅ Reporte #{reporte_id} cerrado automáticamente por validación"
LOG_REPORTE_CERRADO_STAFF = "🔒 Reporte #{reporte_id} cerrado manualmente por staff"
LOG_REPORTE_BANEO = "⛔ Usuario {usuario} baneado temporalmente tras no cumplir reportes"
LOG_REPORTE_EXPULSION = "🚫 Usuario {usuario} expulsado tras reincidir"

# ----------------------------
# ERRORES Y USO INCORRECTO
# ----------------------------

ERROR_AUTO_REPORTE = "❌ No puedes reportarte a ti mismo."
ERROR_NO_MIEMBRO = "❌ Usuario inválido. Debes reportar a un miembro real del servidor."
ERROR_SOLO_BOT = "❌ El canal es solo para uso del bot y reportes automáticos. Tu mensaje ha sido eliminado."
ERROR_SOLO_BOTON = "❌ Solo puedes interactuar con los botones si eres parte del reporte."

# ----------------------------
# INSTRUCCIONES PARA STAFF / PANEL
# ----------------------------

PANEL_TITULO = "Panel de gestión de reportes"
PANEL_CERRAR = "✅ Cerrar reporte"
PANEL_REABRIR = "🔄 Reabrir reporte"
PANEL_PERDONAR = "🕊️ Perdonar sanción"
PANEL_FORZAR_CIERRE = "⚠️ Forzar cierre"

# ----------------------------
# AYUDA Y COMANDOS
# ----------------------------

AYUDA_MIS_REPORTES = (
    "🔍 **Consulta tus reportes abiertos y el historial de apoyo en X.**\n"
    "Aquí puedes ver el estado actual de cada caso, fechas y acciones tomadas."
)

