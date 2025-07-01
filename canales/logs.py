# canales/logs.py
import discord
from config import CANAL_LOGS # Asumiendo que CANAL_LOGS está definido en config.py

async def registrar_log(description, user, channel, bot):
    """
    Registra un evento o acción en el canal de logs del bot.

    Args:
        description (str): Descripción del evento.
        user (discord.User or discord.Member): Usuario relacionado con el evento.
        channel (discord.TextChannel): Canal donde ocurrió el evento (puede ser None).
        bot (discord.Client): Instancia del bot para obtener el canal de logs.
    """
    log_channel = bot.get_channel(CANAL_LOGS)
    if not log_channel:
        print(f"ADVERTENCIA: Canal de logs con ID {CANAL_LOGS} no encontrado.")
        return

    # Formato del mensaje de log
    log_message = f"**[{discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}]** "
    if user:
        log_message += f"**Usuario:** {user.name} (ID: {user.id}) "
    if channel:
        log_message += f"**Canal:** #{channel.name} (ID: {channel.id}) "
    
    log_message += f"**Acción:** {description}"

    try:
        await log_channel.send(log_message)
        # print(f"Log registrado en canal {log_channel.name}: {description}") # Solo para depuración
    except discord.Forbidden:
        print(f"ERROR: No tengo permisos para enviar logs en el canal '{log_channel.name}'.")
    except Exception as e:
        print(f"ERROR inesperado al enviar log: {e}")

# Este módulo no es un cog, por lo tanto, no necesita una función setup().
