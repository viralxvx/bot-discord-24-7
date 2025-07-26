# startup/post_fijado.py

import discord
from config import get_env_int
from mensajes.testimonios_mensaje import MENSAJE_ANCLADO
from utils.redis_conn import redis_conn

CANAL_TESTIMONIOS = get_env_int("CANAL_TESTIMONIOS")

async def publicar_mensaje_anclado(bot):
    canal = bot.get_channel(CANAL_TESTIMONIOS)
    if canal is None:
        print("❌ Canal de testimonios no encontrado.")
        return

    mensaje_id = redis_conn.get("vx:mensaje_anclado_testimonios")

    try:
        if mensaje_id:
            mensaje = await canal.fetch_message(int(mensaje_id))
            await mensaje.edit(content=MENSAJE_ANCLADO)
            print("🔄 Mensaje anclado actualizado correctamente.")
        else:
            nuevo = await canal.send(MENSAJE_ANCLADO)
            await nuevo.pin()
            redis_conn.set("vx:mensaje_anclado_testimonios", nuevo.id)
            print("📌 Mensaje anclado publicado y fijado.")
    except discord.NotFound:
        nuevo = await canal.send(MENSAJE_ANCLADO)
        await nuevo.pin()
        redis_conn.set("vx:mensaje_anclado_testimonios", nuevo.id)
        print("📌 Mensaje anclado creado nuevamente.")
    except Exception as e:
        print(f"❌ Error al publicar mensaje anclado: {e}")

