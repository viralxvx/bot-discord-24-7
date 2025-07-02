import discord
# --- ¡CORRECCIÓN CLAVE AQUÍ! ---
# Asegúrate de importar CANAL_LOGS_ID, NO CANAL_LOGS
from config import CANAL_LOGS_ID 

async def registrar_log(description, user, channel, bot):
    # Asegúrate de que el bot tenga el atributo 'guilds' inicializado
    if not bot.guilds:
        print("Advertencia: El bot aún no ha cargado los guilds. No se puede registrar el log.")
        return

    # Buscar el servidor usando la ID del gremio desde config (si es necesario)
    # Aquí estamos asumiendo que el bot está en un solo servidor principal o que el guild_id
    # del canal es suficiente para encontrar el guild.
    target_guild = None
    if channel and channel.guild:
        target_guild = channel.guild
    elif bot.guilds:
        # Si no hay canal o guild en el canal, intentar obtener el primer guild del bot
        target_guild = bot.guilds[0] 
        print(f"DEBUG: Usando el primer guild del bot para el log: {target_guild.name}")
    
    if not target_guild:
        print("ERROR: No se pudo determinar el guild para registrar el log.")
        return

    # Obtener el canal de logs usando la ID de config
    # --- Asegúrate de usar CANAL_LOGS_ID aquí también ---
    log_channel = discord.utils.get(target_guild.channels, id=CANAL_LOGS_ID)
    
    if not log_channel:
        print(f"ERROR: No se pudo encontrar el canal de logs con ID {CANAL_LOGS_ID} en el servidor {target_guild.name}.")
        return

    embed = discord.Embed(
        title="Registro del Bot",
        description=description,
        color=discord.Color.blue()
    )

    if user:
        embed.add_field(name="Usuario", value=f"{user.display_name} (ID: {user.id})", inline=False)
    
    if channel:
        embed.add_field(name="Canal", value=f"#{channel.name} (ID: {channel.id})", inline=False)
    
    embed.set_footer(text=f"Timestamp: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    try:
        await log_channel.send(embed=embed)
        print(f"Log registrado en Discord: '{description}'")
    except discord.Forbidden:
        print(f"ERROR: No tengo permisos para enviar mensajes en el canal de logs (ID: {CANAL_LOGS_ID}).")
    except Exception as e:
        print(f"ERROR inesperado al enviar log a Discord: {e}")
