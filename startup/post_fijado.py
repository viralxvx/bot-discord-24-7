# startup/post_fijado.py

import discord
from config import get_env_int
from mensajes.testimonios_mensaje import MENSAJE_ANCLADO
from mensajes.pdf_mensajes import get_panel_bienvenida_pdf
from utils.redis_conn import redis_conn

CANAL_TESTIMONIOS = get_env_int("CANAL_TESTIMONIOS")
CANAL_PDF = get_env_int("CANAL_PDF")

async def publicar_mensaje_anclado(bot):
    # Publicar mensaje anclado en el canal de testimonios
    await _publicar_unico_mensaje(
        bot=bot,
        canal_id=CANAL_TESTIMONIOS,
        redis_key="vx:mensaje_anclado_testimonios",
        contenido=MENSAJE_ANCLADO,
        nombre="testimonios"
    )

    # Publicar mensaje anclado en el canal de PDF
    await _publicar_unico_mensaje(
        bot=bot,
        canal_id=CANAL_PDF,
        redis_key="vx:mensaje_anclado_pdf",
        contenido=get_panel_bienvenida_pdf(),
        nombre="PDF"
    )

async def _publicar_unico_mensaje(bot, canal_id, redis_key, contenido, nombre):
    canal = bot.get_channel(canal_id)
    if canal is None:
        print(f"❌ Canal de {nombre} no encontrado.")
        return

    mensaje_id = redis_conn.get(redis_key)

    try:
        if mensaje_id:
            mensaje = await canal.fetch_message(int(mensaje_id))
            await mensaje.edit(content=contenido)
            print(f"🔄 Mensaje anclado de {nombre} actualizado correctamente.")
        else:
            nuevo = await canal.send(contenido)
            await nuevo.pin()
            redis_conn.set(redis_key, nuevo.id)
            print(f"📌 Mensaje anclado de {nombre} publicado y fijado.")
    except discord.NotFound:
        nuevo = await canal.send(contenido)
        await nuevo.pin()
        redis_conn.set(redis_key, nuevo.id)
        print(f"📌 Mensaje anclado de {nombre} creado nuevamente.")
    except Exception as e:
        print(f"❌ Error al publicar mensaje anclado en {nombre}: {e}")
