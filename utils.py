import re
import asyncio
from datetime import datetime

# Mensajes de normas y anuncios
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

def calcular_calificacion(faltas):
    porcentaje = max(0, 100 - faltas)
    barras = int(porcentaje // 10)
    barra_visual = "[" + "█" * barras + " " * (10 - barras) + "]"
    return porcentaje, f"{barra_visual} {porcentaje:.2f}%"

async def actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, estado):
    try:
        calificacion, barra_visual = calcular_calificacion(faltas)
        contenido = (
            f"👤 **Usuario**: {miembro.mention}\n"
            f"📊 **Faltas en #🧵go-viral**: {faltas} {'👻' if faltas > 0 else ''}\n"
            f"✅ **Aciertos**: {aciertos}\n"
            f"📈 **Calificación**: {barra_visual}\n"
            f"🚨 **Estado de Inactividad**: {estado}\n"
        )
        mensaje_id = faltas_dict[miembro.id]["mensaje_id"]
        if mensaje_id:
            try:
                mensaje = await canal_faltas.fetch_message(mensaje_id)
                if mensaje.content != contenido:
                    await mensaje.edit(content=contenido)
            except discord.errors.NotFound:
                mensaje = await canal_faltas.send(contenido)
                faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
        else:
            mensaje = await canal_faltas.send(contenido)
            faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
    except Exception:
        pass

async def registrar_log(texto, categoria="general"):
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if canal_log and texto:
        try:
            # Acortar texto si es demasiado largo
            if len(texto) > MAX_LOG_LENGTH:
                texto = texto[:MAX_LOG_LENGTH] + "..."
                
            # Formato compacto de timestamp
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
            await canal_log.send(f"[{timestamp}] [{categoria.upper()}] {texto}")
        except:
            pass

async def batch_log(messages):
    """Envía logs en batches con delay para evitar rate limiting"""
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if not canal_log:
        return
        
    for batch in messages:
        if not batch:
            continue
            
        # Combinar múltiples mensajes en uno solo
        combined = "\n".join(batch)
        try:
            await canal_log.send(combined)
        except:
            pass
        
        # Esperar antes del próximo batch
        await asyncio.sleep(LOG_BATCH_DELAY)

async def publicar_mensaje_unico(canal, contenido, pinned=False):
    try:
        contenido_normalizado = contenido.strip().lower()
        mensajes_vistos = set()
        mensajes_a_eliminar = []
        async for msg in canal.history(limit=None):
            msg_normalizado = msg.content.strip().lower()
            if msg.author == bot.user:
                if msg_normalizado == contenido_normalizado or msg_normalizado in mensajes_vistos:
                    mensajes_a_eliminar.append(msg)
            if pinned and msg.pinned and msg.author == bot.user:
                mensajes_a_eliminar.append(msg)
        for msg in mensajes_a_eliminar:
            try:
                await msg.delete()
            except:
                pass
        mensaje = await canal.send(contenido)
        if pinned:
            await mensaje.pin()
        return mensaje
    except:
        return None
