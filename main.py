# main.py
import discord
from discord.ext import commands
import os
from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from state_management import RedisState # Importamos RedisState

# Configuración de intents para el bot
intents = discord.Intents.default()
intents.message_content = True # Permite al bot leer el contenido de los mensajes
intents.members = True         # Necesario para el evento on_member_join

# Inicializa el bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name} (ID: {bot.user.id})')
    print('------')

    # Inicializa RedisState para que esté disponible en la función on_ready
    redis_state = RedisState() 
    bot.redis_state = redis_state # Guarda una referencia en el bot si lo necesitas globalmente

    # Cargar todos los cogs dinámicamente
    await load_cogs()

    # Llamar a la lógica on_ready del cog GoViralCog
    # Esto asegura que el mensaje de bienvenida se gestione al iniciar/reiniciar el bot
    go_viral_cog = bot.get_cog("GoViralCog")
    if go_viral_cog:
        await go_viral_cog.go_viral_on_ready()
    else:
        print("ERROR: GoViralCog no encontrado. El mensaje de bienvenida no se gestionará.")

    # Puedes agregar aquí lógica de estado o actividad del bot
    await bot.change_presence(activity=discord.Game(name="Monitoreando el Go-Viral"))


# Cargar cogs (extensiones)
async def load_cogs():
    # Cogs existentes
    await bot.load_extension("canales.go_viral")
    await bot.load_extension("canales.logs")
    await bot.load_extension("canales.faltas")
    # Nuevo Cog para el canal de presentación
    await bot.load_extension("canales.presentate") # <--- ESTA LÍNEA ES CLAVE PARA EL CANAL 'PRESENTATE'

    print("All cogs loaded.")

# Ejecutar el bot
if __name__ == "__main__":
    # Inicializar el cliente Redis aquí si no se hace en RedisState directamente
    # Esto asegura que Redis esté listo antes de que los cogs lo utilicen.
    redis_state_instance = RedisState() 
    # Puedes probar la conexión aquí si quieres
    try:
        redis_state_instance.redis_client.ping()
        print("Conexión a Redis exitosa.")
    except Exception as e:
        print(f"Error al conectar a Redis: {e}")
        # Considera cómo quieres manejar este error: salir, reintentar, etc.

    bot.run(BOT_TOKEN)
