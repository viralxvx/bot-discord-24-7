# utils/cleanup.py

import asyncio
import discord
from utils.logger import custom_log

async def limpiar_canal_tras_una_hora(bot, canal_id: int, mensaje_bienvenida_id: int):
    """
    Espera una hora y luego limpia el canal, dejando solo el mensaje de bienvenida anclado.
    """
    await asyncio.sleep(3600)  # Esperar 1 hora

    canal = bot.get_channel(canal_id)
    if not canal:
        custom_log(bot, "CLEANUP", "ERROR", f"❌ No se encontró el canal con ID: {canal_id}")
        return

    try:
        mensajes = [m async for m in canal.history(limit=100)]
        for mensaje in mensajes:
            if mensaje.id != mensaje_bienvenida_id:
                await mensaje.delete()

        custom_log(bot, "CLEANUP", "INFO", f"🧹 Canal {canal.name} limpiado. Solo queda el mensaje de bienvenida.")
    except Exception as e:
        custom_log(bot, "CLEANUP", "ERROR", f"❌ Error al limpiar canal {canal_id}: {e}")
