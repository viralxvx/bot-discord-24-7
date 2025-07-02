import discord
from discord.ext import commands
import os
import asyncio
from state_management import RedisState
from canales.go_viral import GoViralCog
from canales.logs import registrar_log

# --- Configuración del Bot ---
TOKEN = os.getenv('DISCORD_TOKEN') # ¡CONFIRMADO: DISCORD_TOKEN!
REDIS_URL = os.getenv('REDIS_URL')
# No intentamos convertir GUILD_ID a int aquí, lo hacemos más abajo si existe
GUILD_ID_STR = os.getenv('GUILD_ID') 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Necesario para eventos de miembros, como on_member_join
intents.reactions = True # Necesario para eventos de reacciones
intents.guilds = True # Necesario para bot.guilds en on_ready y para obtener el objeto guild

bot = commands.Bot(command_prefix='!', intents=intents)

# --- Evento on_ready ---
@bot.event
async def on_ready():
    print(f'🟢Bot conectado como {bot.user} (ID: {bot.user.id})')
    print('------')

    # Intentar registrar la conexión en el canal de logs de Discord
    try:
        await registrar_log(f"El bot se ha conectado y está en línea.", bot.user, None, bot)
        print("Log de conexión enviado a Discord.")
    except Exception as e:
        print(f"ERROR CRÍTICO: No se pudo enviar el log de conexión a Discord: {e}")
        # Si el log de conexión falla, es un problema serio con el canal o permisos.
        # El bot intentará continuar, pero ten en cuenta este error.

    # 1. Conectar a Redis y adjuntarlo al bot
    try:
        if not REDIS_URL:
            raise ValueError("La variable de entorno REDIS_URL no está configurada. El bot no puede operar sin Redis.")
        
        bot.redis_state = RedisState(REDIS_URL)
        print("Conexión a Redis establecida y adjuntada al bot.")
        await registrar_log("Conexión a Redis establecida.", bot.user, None, bot)

    except Exception as e:
        print(f"ERROR FATAL: No se pudo conectar a Redis al inicio: {e}")
        await registrar_log(f"ERROR FATAL: Fallo al conectar a Redis: {e}. El bot se desconectará.", bot.user, None, bot)
        await bot.close() 
        return 

    # 2. Cargar Cogs
    try:
        await bot.load_extension('canales.go_viral') # Usar load_extension con string
        print("Cog 'canales.go_viral' cargado.")
        await registrar_log("Cog 'canales.go_viral' cargado.", bot.user, None, bot)

        # Si el cog tiene un on_ready personalizado, llamarlo explícitamente
        go_viral_cog = bot.get_cog('GoViralCog')
        if go_viral_cog:
            await go_viral_cog.go_viral_on_ready()
            print("Lógica on_ready de GoViralCog ejecutada.")
            await registrar_log("Lógica de inicio de GoViralCog ejecutada.", bot.user, None, bot)
        
        print('Todos los cogs cargados y listos.')
        await registrar_log("Todos los cogs cargados y listos.", bot.user, None, bot)

    except Exception as e:
        print(f"ERROR FATAL: Al cargar o inicializar cogs: {e}")
        await registrar_log(f"ERROR FATAL: Fallo al cargar cogs: {e}. El bot se desconectará.", bot.user, None, bot)
        await bot.close() 
        return

    # Lógica para sincronizar comandos de barra (slash commands)
    try:
        if GUILD_ID_STR: # Solo si la variable de entorno GUILD_ID existe
            try:
                guild_id_int = int(GUILD_ID_STR) # Intentar convertir a int
                guild = discord.Object(id=guild_id_int)
                bot.tree.copy_global_commands()
                await bot.tree.sync(guild=guild)
                print(f"Comandos de barra sincronizados para el gremio {GUILD_ID_STR}.")
                await registrar_log(f"Comandos de barra sincronizados para el gremio {GUILD_ID_STR}.", bot.user, None, bot)
            except ValueError:
                print(f"ADVERTENCIA: GUILD_ID '{GUILD_ID_STR}' no es un número válido. Sincronizando comandos de barra globalmente.")
                await registrar_log(f"ADVERTENCIA: GUILD_ID no válido. Sincronizando comandos de barra globalmente.", bot.user, None, bot)
                await bot.tree.sync() # Sincronizar globalmente si GUILD_ID no es válido
                print("Comandos de barra globales sincronizados.")
        else: # Si GUILD_ID_STR es None (no configurado)
            print("ADVERTENCIA: GUILD_ID no configurado. Sincronizando comandos de barra globalmente.")
            await bot.tree.sync() # Sincronizar globalmente si no hay GUILD_ID
            print("Comandos de barra globales sincronizados.")
            await registrar_log("ADVERTENCIA: GUILD_ID no configurado. Comandos de barra globales sincronizados.", bot.user, None, bot)
    except Exception as e:
        print(f"ERROR al sincronizar comandos de barra: {e}")
        await registrar_log(f"ERROR: Fallo al sincronizar comandos de barra: {e}.", bot.user, None, bot)

    print(f"{bot.user.name} está listo para operar en {len(bot.guilds)} servidores.")
    for guild in bot.guilds:
        print(f'Operando en el servidor: {guild.name} (ID: {guild.id})')


# --- Evento on_message ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return # Ignorar mensajes del propio bot

    await bot.process_commands(message)

# --- Ejecutar el Bot ---
async def main():
    async with bot:
        discord_token = os.getenv('DISCORD_TOKEN')
        redis_url = os.getenv('REDIS_URL')

        if not discord_token:
            print("Error: La variable de entorno DISCORD_TOKEN no está configurada. El bot no puede iniciar.")
            return

        if not redis_url:
            print("Error: La variable de entorno REDIS_URL no está configurada. El bot no puede operar sin Redis.")
            return

        try:
            await bot.start(discord_token)
        except discord.LoginFailure:
            print("Error: El token del bot es inválido. Por favor, verifica tu DISCORD_TOKEN en las variables de entorno de Railway.")
        except Exception as e:
            print(f"Error inesperado al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
