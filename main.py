import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from canales.logs import registrar_log
from state_management import RedisState # Importar RedisState
import asyncio
import config # Importar config para acceder a las IDs

# Cargar variables de entorno del archivo .env
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
        # ¡CORRECCIÓN CLAVE AQUÍ! Pasar redis_url explícitamente.
        if not config.REDIS_URL:
            raise ValueError("REDIS_URL no está configurada en config.py o en las variables de entorno de Railway.")
        
        bot.redis_state = RedisState(redis_url=config.REDIS_URL) 
        # La conexión y el ping ya se hacen dentro de RedisState.__init__
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
        await registrar_log("El bot se ha desconectado de Discord.", bot.user, None, bot)
    except Exception as e:
        print(f"Error al intentar registrar log de desconexión: {e}")

# --- Evento on_message ---
@bot.event
async def on_message(message):
    await bot.process_commands(message)

# --- Ejecutar el bot ---
async def main():
    if not config.DISCORD_BOT_TOKEN:
        print("Error: DISCORD_TOKEN no está configurado. Asegúrate de tenerlo en las variables de entorno de Railway.")
        return

    try:
        await bot.start(config.DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("Error: El token del bot es inválido. Por favor, verifica tu DISCORD_TOKEN en las variables de entorno.")
    except Exception as e:
        print(f"Error inesperado al iniciar el bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
