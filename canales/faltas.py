import discord
import asyncio
from config import CANAL_FALTAS_ID # ¡CORRECCIÓN CLAVE AQUÍ! Asegúrate de que sea CANAL_FALTAS_ID
from canales.logs import registrar_log # Importar la función de logs

async def registrar_falta(user: discord.Member, reason: str, channel: discord.TextChannel, bot):
    """Registra una falta en el canal de faltas y envía una advertencia al usuario."""
    
    # Obtener el canal de faltas
    faltas_channel = None
    try:
        faltas_channel = await bot.fetch_channel(CANAL_FALTAS_ID)
    except discord.NotFound:
        print(f"ERROR: El canal de faltas con ID {CANAL_FALTAS_ID} no fue encontrado.")
        await registrar_log(f"ERROR: Canal de faltas no encontrado (ID: {CANAL_FALTAS_ID})", bot.user, channel, bot)
        return
    except discord.Forbidden:
        print(f"ERROR: No tengo permisos para acceder al canal de faltas con ID {CANAL_FALTAS_ID}.")
        await registrar_log(f"ERROR: Permisos denegados para canal de faltas (ID: {CANAL_FALTAS_ID})", bot.user, channel, bot)
        return
    except Exception as e:
        print(f"ERROR inesperado al buscar el canal de faltas: {e}")
        await registrar_log(f"ERROR: Fallo al buscar canal de faltas: {e}", bot.user, channel, bot)
        return

    if not faltas_channel:
        print(f"ERROR: No se pudo obtener el objeto del canal de faltas con ID: {CANAL_FALTAS_ID}.")
        return

    embed = discord.Embed(
        title="🚨 Falta Registrada 🚨",
        description=f"Se ha registrado una falta para **{user.display_name}**.",
        color=discord.Color.red()
    )
    embed.add_field(name="Usuario", value=f"{user.mention} (ID: {user.id})", inline=False)
    embed.add_field(name="Razón", value=reason, inline=False)
    embed.add_field(name="Canal Original", value=f"#{channel.name} (ID: {channel.id})", inline=False)
    embed.set_footer(text=f"Timestamp: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    try:
        await faltas_channel.send(embed=embed)
        print(f"Falta registrada para {user.name} en el canal de faltas: {reason}")
        await registrar_log(f"Falta registrada para {user.name}: {reason}", user, channel, bot)
    except discord.Forbidden:
        print(f"ERROR: No tengo permisos para enviar mensajes en el canal de faltas (ID: {CANAL_FALTAS_ID}).")
        await registrar_log(f"ERROR: No hay permisos para enviar en canal de faltas (ID: {CANAL_FALTAS_ID})", bot.user, channel, bot)
    except Exception as e:
        print(f"ERROR inesperado al enviar la falta a Discord: {e}")
        await registrar_log(f"ERROR: Fallo al enviar falta a Discord: {e}", bot.user, channel, bot)

    await enviar_advertencia(user, reason, bot)


async def enviar_advertencia(user: discord.Member, reason: str, bot):
    """Envía una advertencia por DM al usuario."""
    dm_message = (
        f"🚨 **Advertencia de {bot.user.name}** 🚨\n\n"
        f"Se te ha registrado una falta por la siguiente razón: **{reason}**\n\n"
        "Por favor, revisa las reglas del canal y asegúrate de cumplirlas para evitar futuras sanciones."
    )
    try:
        if user.dm_channel is None:
            await user.create_dm()
        await user.send(dm_message)
        print(f"Advertencia enviada por DM a {user.name}.")
        await registrar_log(f"Advertencia por DM enviada a {user.name}: {reason}", bot.user, None, bot)
    except discord.Forbidden:
        print(f"Error: No se pudo enviar DM de advertencia a {user.name}. Puede que tenga los DMs deshabilitados.")
        await registrar_log(f"ERROR: No se pudo enviar DM a {user.name} (DMs deshabilitados)", bot.user, None, bot)
    except Exception as e:
        print(f"Error inesperado al enviar DM de advertencia a {user.name}: {e}")
        await registrar_log(f"ERROR: Fallo al enviar DM de advertencia: {e}", bot.user, None, bot)
