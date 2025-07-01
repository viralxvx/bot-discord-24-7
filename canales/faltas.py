# canales/faltas.py
import discord
from config import CANAL_FALTAS, CANAL_OBJETIVO
from canales.logs import registrar_log # Importa la función de logs

async def enviar_advertencia(user, reason, channel):
    """
    Envía una advertencia por DM al usuario y registra en el canal de faltas.
    """
    embed = discord.Embed(
        title="⚠️ Advertencia de Infracción ⚠️",
        description=f"Has recibido una advertencia en el canal {channel.mention} por la siguiente razón:",
        color=discord.Color.red()
    )
    embed.add_field(name="Razón", value=reason, inline=False)
    embed.add_field(name="Canal Afectado", value=f"#{channel.name}", inline=False)
    embed.set_footer(text="Por favor, revisa las reglas para evitar futuras sanciones.")

    try:
        if user.dm_channel is None:
            await user.create_dm()
        await user.send(embed=embed)
        print(f"Advertencia enviada por DM a {user.name} por '{reason}'.")
    except discord.Forbidden:
        print(f"Error: No se pudo enviar DM de advertencia a {user.name}. Puede que tenga los DMs deshabilitados.")
    except Exception as e:
        print(f"Error inesperado al enviar advertencia por DM a {user.name}: {e}")

async def registrar_falta(user, reason, channel):
    """
    Registra una falta para un usuario en el canal de faltas y notifica al usuario.
    """
    # Usar CANAL_FALTAS del config.py
    faltas_channel = channel.guild.get_channel(CANAL_FALTAS)
    
    if not faltas_channel:
        print(f"ERROR: No se encontró el canal de faltas con ID {CANAL_FALTAS}.")
        await registrar_log(f"ERROR: No se encontró el canal de faltas ID: {CANAL_FALTAS} para registrar falta de {user.name}.", user, channel, channel.guild.me)
        return

    falta_message = f"**Falta Registrada:** Usuario: {user.name} (ID: {user.id}) | Razón: {reason} | Canal: #{channel.name}"

    try:
        await faltas_channel.send(falta_message)
        print(f"Falta de {user.name} registrada en #{faltas_channel.name}: {reason}")
        await registrar_log(f"Falta registrada: {reason}", user, channel, channel.guild.me) # 'channel.guild.me' es la instancia del bot
    except discord.Forbidden:
        print(f"ERROR: No tengo permisos para enviar mensajes en el canal de faltas '{faltas_channel.name}'.")
    except Exception as e:
        print(f"ERROR inesperado al registrar falta: {e}")
    
    await enviar_advertencia(user, reason, channel)

# Este módulo no es un cog, por lo tanto, no necesita una función setup().
