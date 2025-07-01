# notificaciones/go_viral.py

URL_INVALIDA = "**Error:** La URL no es válida. Usa el formato: `https://x.com/usuario/status/123456...`"
INTERVALO_NO_RESPETADO = "**Error:** Debes esperar al menos 2 publicaciones válidas de otros usuarios antes de publicar nuevamente."
REACCIONES_PENDIENTES_CHANNEL = "**Error:** Debes reaccionar con 🔥 a las siguientes publicaciones antes de publicar:\n{missing_info_str}"
REACCIONES_PENDIENTES_DM = "⚠️ **Tienes reacciones 🔥 pendientes en el canal {channel_name}**.\nDebes apoyar estas publicaciones en 𝕏 y reaccionar con 🔥 en Discord antes de volver a publicar:\n{missing_info_str}\n\n*Este es un mensaje automático del bot.*"
LINK_CORREGIDO_CHANNEL = "**¡Link corregido!** Tu publicación se ha ajustado al formato correcto. Por favor, recuerda usar `https://x.com/usuario/status/ID` sin parámetros adicionales para futuras publicaciones."
NO_REACCION_THUMBS_UP = "**Error:** No reaccionaste con 👍 a tu publicación en 120 segundos. Mensaje eliminado."
REACCION_FIRE_PROPIA_PUBLICACION = "**Error:** No puedes reaccionar con 🔥 a tu propia publicación."
REACCION_NO_PERMITIDA = "**Atención:** Solo se permiten reacciones 👍 y 🔥 en este canal. Tu reacción ha sido eliminada."
