# utils/discord_tools.py

import discord

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
        mensaje = await canal.send(f"🔄 **{titulo}**\n0% [░░░░░░░░░░]")
        return mensaje
    except Exception as e:
        print(f"❌ Error al crear mensaje de progreso: {e}")
        return None
