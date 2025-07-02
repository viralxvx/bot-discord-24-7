# main.py

import discord
from discord.ext import commands
import asyncio
import os # Para variables de entorno

# Importar configuraciones
import config

# Importar la clase RedisState
from state_management import RedisState

# Importar los nuevos cogs
from cogs.faltas_manager import FaltasManager
from cogs.inactivity_tracker import InactivityTracker
from cogs.support_proroga import SupportProroga

# --- Configuración de Intenciones ---
# Es CRÍTICO tener las intenciones correctas.
# Necesitas al menos: default, members, message_content.
intents = discord.Intents.default()
intents.members = True          # Necesario para on_member_remove, guild.members
intents.message_content = True  # Necesario para leer el contenido de los mensajes (si tienes comandos de texto antiguos, etc.)

# --- Creación de la Instancia del Bot ---
# Reemplaza '!' con tu prefijo de comando actual si es diferente
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Evento on_ready ---
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name} (ID: {bot.user.id})')
    print('------')

    # Almacenar la instancia del gremio principal si tienes uno solo
    # o si quieres que el bot opere en un gremio específico.
    # Reemplaza GUILD_ID_PRINCIPAL con la ID de tu servidor si lo necesitas
    # bot.guild_id = 000000000000000000 # ¡REEMPLAZA ESTO CON LA ID DE TU SERVIDOR!
    # Opcional: Si el bot solo estará en un servidor, puedes obtenerlo así:
    if len(bot.guilds) > 0:
        bot.guild_id = bot.guilds[0].id # Toma el ID del primer servidor en el que está
        print(f"Operando en el servidor: {bot.guilds[0].name} (ID: {bot.guild_id})")
    else:
        print("¡El bot no está en ningún servidor! Invítalo a tu servidor.")
        return # Si el bot no está en un servidor, no hay nada que hacer.

    # Conectar a Redis
    try:
        bot.redis_state = RedisState(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD
        )
        print("RedisState inicializado.")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a Redis: {e}")
        # Considera salir o manejar este error críticamente si Redis es indispensable

    # Cargar los cogs (en orden de dependencia si la hay)
    try:
        # El orden es importante: FaltasManager necesita estar cargado para InactivityTracker
        # y ambos para SupportProroga (para actualizar tarjetas)
        await bot.load_extension('cogs.faltas_manager')
        print("Cog FaltasManager cargado.")
        await bot.load_extension('cogs.inactivity_tracker')
        print("Cog InactivityTracker cargado.")
        await bot.load_extension('cogs.support_proroga')
        print("Cog SupportProroga cargado.")
    except Exception as e:
        print(f"ERROR al cargar un cog: {e}")
        # Log this error to a file or a Discord channel if possible

    # Opcional: Sincronizar comandos de barra (slash commands) si los usas
    # await bot.tree.sync()
    # print("Comandos de barra sincronizados.")

    print(f'{bot.user.name} está listo para operar!')


# --- Evento on_message (Para tu lógica existente de GoViral) ---
# Si ya tienes un on_message para el canal GoViral, asegúrate de que no entre en conflicto.
# La nueva implementación de on_message en 'faltas_manager.py' solo afecta a #faltas.
# Si tu lógica actual está en main.py, asegúrate de que no interfiera.
# Por ejemplo, si tienes algo como esto:
@bot.event
async def on_message(message):
    # Ignorar mensajes del propio bot
    if message.author == bot.user or message.author.bot:
        return

    # Si el mensaje es en el canal GoViral (para guardar last_post_time)
    if message.channel.id == config.CANAL_GO_VIRAL_ID:
        # Asume que esta es tu lógica actual para validar y guardar el último post
        # Por ejemplo:
        if "http" in message.content: # Simplemente un ejemplo de validación
            await bot.redis_state.set_last_post_time(message.author.id, get_current_timestamp())
            # Puedes añadir más lógica de validación de URL, reacciones, etc.
            # Y luego, si hay una falta menor, llamar a faltas_manager.update_user_fault_card
            # faltas_manager = bot.get_cog("FaltasManager")
            # if faltas_manager:
            #     await faltas_manager.update_user_fault_card(
            #         user=message.author,
            #         status="activo", # O "falta_menor" si hay una falta pero no es de inactividad
            #         last_post_time=get_current_timestamp(),
            #         new_fault_details={"timestamp": get_current_timestamp(), "reason": "URL inválida"} # Si aplica
            #     )

    # Importante: Procesar comandos de la vieja API si los sigues usando
    await bot.process_commands(message)


# --- Ejemplo de Comando de Administrador para Limpieza (Solo para uso inicial) ---
# Este comando es para ser usado **una única vez** para limpiar el canal #faltas antes de que el nuevo sistema inicie completamente.
# Ejecútalo en un canal de administración, NO en #faltas.
@bot.command()
@commands.has_permissions(administrator=True)
async def limpiar_faltas_historial(ctx):
    """
    [ADMIN] Limpia todos los mensajes en #faltas y resetea el historial de tarjetas en Redis.
    Útil para el setup inicial del nuevo sistema.
    """
    if ctx.channel.id == config.CANAL_FALTAS_ID:
        await ctx.send("🚨 ¡ADVERTENCIA! Este comando NO debe ejecutarse directamente en el canal #faltas. Por favor, úsalo en un canal de administración.", ephemeral=True)
        return

    await ctx.send("¡ADVERTENCIA! Esto eliminará **TODOS** los mensajes en el canal #faltas y reseteará los datos de tarjetas de faltas en Redis. "
                   "**Esta acción es irreversible.**\n\n"
                   "Para confirmar, escribe `confirmar limpieza faltas` en los próximos 30 segundos.")

    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'confirmar limpieza faltas', timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo agotado. La operación de limpieza ha sido cancelada.")

    faltas_channel = bot.get_channel(config.CANAL_FALTAS_ID)
    if not faltas_channel:
        return await ctx.send(f"Error: El canal de faltas (ID: `{config.CANAL_FALTAS_ID}`) no fue encontrado.")

    await ctx.send(f"Iniciando limpieza del canal {faltas_channel.mention} y de los datos de Redis...", ephemeral=False)
    
    try:
        # Borrar todos los mensajes del canal
        await faltas_channel.purge(limit=None)
        await asyncio.sleep(2) # Dar un pequeño respiro a la API
        
        # Limpiar Redis
        await bot.redis_state.clear_all_fault_card_message_ids()
        await bot.redis_state.set_faltas_panel_message_id(None) # Resetear ID del panel si quieres que se recree
        
        # Opcional: Re-enviar el mensaje del panel después de limpiar
        faltas_manager_cog = bot.get_cog("FaltasManager")
        if faltas_manager_cog:
            await faltas_manager_cog.setup_faltas_channel() # Esto recreará el panel y sincronizará
        
        await ctx.send(f"✅ Canal {faltas_channel.mention} limpiado y datos de faltas en Redis reseteados. El sistema de tarjetas de faltas ha sido reinicializado.")
    except discord.Forbidden:
        await ctx.send(f"🚨 ERROR: No tengo permisos para borrar mensajes en {faltas_channel.mention} o para realizar acciones en Redis. Asegúrate de tener los permisos correctos.")
    except Exception as e:
        await ctx.send(f"🚨 Ocurrió un error inesperado durante la limpieza: {e}")
        print(f"Error durante limpieza de faltas: {e}")


# --- Ejecutar el Bot ---
# Asegúrate de que tu DISCORD_BOT_TOKEN esté en tus variables de entorno
if __name__ == "__main__":
    if config.DISCORD_BOT_TOKEN is None:
        print("ERROR: La variable de entorno DISCORD_BOT_TOKEN no está configurada.")
        print("Por favor, establece la variable DISCORD_BOT_TOKEN con el token de tu bot.")
        exit(1)
    bot.run(config.DISCORD_BOT_TOKEN)
