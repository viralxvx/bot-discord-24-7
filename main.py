import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from canales.logs import registrar_log
from state_management import RedisState # Importar RedisState
import asyncio
import config # Importar config para acceder a las IDs

# Cargar variables de entorno del archivo .env
# Esto es más relevante en desarrollo local, Railway ya las inyecta
load_dotenv()

# Configurar intents para el bot
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.members = True
intents.guilds = True # Necesario para bot.guilds en on_ready y para ver miembros

# Inicializar el bot
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Evento on_ready ---
@bot.event
async def on_ready():
    print(f'🟢Bot conectado como {bot.user} (ID: {bot.user.id})')
    print('------')

    # 1. Conectar a Redis y adjuntarlo al bot
    try:
        # Aquí se inicializa RedisState. No necesita argumentos porque los obtiene de os.getenv.
        bot.redis_state = RedisState() 
        # Ya el constructor de RedisState() llama a _get_redis_client() que hace el ping.
        # No necesitas un método .connect() aparte si el ping ya se hace en la inicialización.
        print("Conexión a Redis establecida y adjuntada al bot.")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a Redis al inicio: {e}")
        # Si Redis es crítico, puedes optar por detener el bot aquí.
        # await bot.close() 
        # return 

    # 2. Cargar Cogs
    try:
        # Cargar el cog de Go Viral
        await bot.load_extension('canales.go_viral')
        print("Cog 'canales.go_viral' cargado.")
        
        # Llama a la función on_ready específica del cog GoViralCog
        go_viral_cog = bot.get_cog('GoViralCog')
        if go_viral_cog:
            await go_viral_cog.go_viral_on_ready()
            print("Lógica on_ready de GoViralCog ejecutada.")
        
        print('Todos los cogs cargados y listos.')

        # Imprimir servidores donde opera el bot
        for guild in bot.guilds:
            print(f'Operando en el servidor: {guild.name} (ID: {guild.id})')
        print(f"{bot.user.name} está listo para operar!")

    except Exception as e:
        print(f'ERROR al cargar o inicializar cogs: {e}')
        # Es posible que el bot se detenga si los cogs no cargan.
        # await bot.close()


# --- Evento on_disconnect ---
@bot.event
async def on_disconnect():
    print("Bot desconectado.")
    try:
        # Asegúrate de que registrar_log reciba el objeto bot.
        # Si el bot ya está desconectado, puede que no pueda enviar logs a Discord.
        # Esto es más para un registro interno o a la consola/stdout de Railway.
        await registrar_log("El bot se ha desconectado de Discord.", bot.user, None, bot)
    except Exception as e:
        print(f"Error al intentar registrar log de desconexión: {e}")

# --- Evento on_message ---
# Esto es necesario si no tienes comandos de texto definidos en cogs que usen @commands.command()
# Si tus comandos están todos en cogs, puedes omitir esto.
# Si tienes lógica global de mensajes que no es un comando, déjalo.
@bot.event
async def on_message(message):
    # Asegúrate de que el bot procese los comandos definidos en los cogs
    await bot.process_commands(message)

# --- Ejecutar el bot ---
async def main():
    # El token del bot se obtiene de config.py, que a su vez lo toma de os.getenv.
    # Asegúrate de que config.DISCORD_TOKEN tenga el valor correcto.
    if not config.DISCORD_BOT_TOKEN:
        print("Error: DISCORD_TOKEN no está configurado. Asegúrate de tenerlo en las variables de entorno de Railway.")
        return

    try:
        # Esto iniciará el bot y llamará a on_ready() una vez conectado.
        await bot.start(config.DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("Error: El token del bot es inválido. Por favor, verifica tu DISCORD_TOKEN en las variables de entorno.")
    except Exception as e:
        print(f"Error inesperado al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
