# utils/discord_tools.py

import discord
import asyncio

async def actualizar_mensaje_progreso(mensaje: discord.Message, nuevo_texto: str):
    """
    Edita un mensaje existente para actualizar el progreso, evitando múltiples publicaciones.
    """
    try:
        await mensaje.edit(content=nuevo_texto)
    except Exception as e:
        print(f"❌ Error al actualizar mensaje de progreso: {e}")


async def crear_mensaje_progreso(canal: discord.TextChannel, titulo: str) -> discord.Message:
    """
    Envía un mensaje inicial de progreso con formato profesional.
    """
    try:
        mensaje = await canal.send(f"🔄 **{titulo}**\n0% [░░░░░░░░░░░░░░░░░░░░░]")
        return mensaje
    except Exception as e:
        print(f"❌ Error al crear mensaje de progreso: {e}")
        return None


async def limpiar_canal_despues(bot, canal: discord.TextChannel, delay_minutos: int = 60):
    """
    Limpia todos los mensajes del canal (excepto el de bienvenida) después del tiempo indicado.
    """
    await asyncio.sleep(delay_minutos * 60)
    try:
        mensajes = [m async for m in canal.history(limit=100)]
        for m in mensajes:
            if not m.pinned:
                try:
                    await m.delete()
                except:
                    continue
        print(f"🧹 Canal {canal.name} limpiado automáticamente tras {delay_minutos} minutos.")
    except Exception as e:
        print(f"❌ Error al limpiar canal automáticamente: {e}")
