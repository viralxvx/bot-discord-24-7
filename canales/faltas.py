import discord
from config import CANAL_FALTAS
from canales.logs import registrar_log # Importa la función de logs

async def enviar_advertencia(user, reason, channel):
    """
    Envía una advertencia al usuario por DM.
    """
    warning_message = f"🚨 **Advertencia de {channel.guild.name}** 🚨\n\n" \
                      f"Tu acción en el canal #{channel.name} ha resultado en una falta.\n" \
                      f"**Razón:** {reason}\n\n" \
                      f"Por favor, revisa las reglas del canal para evitar futuras faltas.\n\n" \
                      f"*Este es un mensaje automático del bot.*"
    try:
        if user.dm_channel is None:
            await user.create_dm()
        await user.send(warning_message)
        print(f"Advertencia enviada por DM a {user.name}.")
    except discord.Forbidden:
        print(f"Error: No se pudo enviar DM de advertencia a {user.name}. Puede que tenga los DMs deshabilitados.")
    except Exception as e:
        print(f"Error inesperado al enviar DM de advertencia a {user.name}: {e}")

async def registrar_falta(user, reason, channel, bot): # <--- ¡AHORA RECIBE EL OBJETO 'bot' COMPLETO!
    """
    Registra una falta para un usuario en el canal de faltas y notifica al usuario.
    """
    if not bot: # Si por alguna razón el bot no se pasa, es un error
        print("ERROR: Instancia del bot no proporcionada a registrar_falta.")
        return

    faltas_channel = bot.get_channel(CANAL_FALTAS) # Usar el objeto 'bot' pasado para obtener el canal
    
    if not faltas_channel:
        print(f"ERROR: No se encontró el canal de faltas con ID {CANAL_FALTAS}.")
        # ¡IMPORTANTE! Aquí también pasamos el objeto 'bot' correcto
        await registrar_log(f"ERROR: No se encontró el canal de faltas ID: {CANAL_FALTAS} para registrar falta de {user.name}.", user, channel, bot) 
        return

    falta_message = f"**Falta Registrada:** Usuario: {user.name} (ID: {user.id}) | Razón: {reason} | Canal: #{channel.name}"

    try:
        await faltas_channel.send(falta_message)
        print(f"Falta de {user.name} registrada en #{faltas_channel.name}: {reason}")
        # Aquí también pasamos el objeto 'bot'
        await registrar_log(f"Falta registrada: {reason}", user, channel, bot) 
    except discord.Forbidden:
        print(f"ERROR: No tengo permisos para enviar mensajes en el canal de faltas '{faltas_channel.name}'.")
    except Exception as e:
        print(f"ERROR inesperado al registrar falta: {e}")
    
    await enviar_advertencia(user, reason, channel)
