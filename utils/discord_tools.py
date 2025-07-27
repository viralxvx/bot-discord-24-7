# utils/discord_tools.py

import discord

async def actualizar_mensaje(interaction, mensaje_objetivo, nuevo_contenido):
    try:
        await mensaje_objetivo.edit(content=nuevo_contenido)
    except Exception as e:
        await interaction.followup.send(f"❌ Error al actualizar mensaje: {e}", ephemeral=True)
