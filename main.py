# main.py
import discord
from discord.ext import commands
import os
from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from state_management import RedisState 

# Configuración de intents para el bot
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True         

# Inicializa el bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name} (ID: {bot.user.id})')
    print('------')

    redis_state = RedisState() 
    bot.redis_state = redis_state 

    # Cargar todos los cogs dinámicamente
    await load_cogs()

    # Llamar a la lógica on_ready del cog GoViralCog
    go_viral_cog = bot.get_cog("GoViralCog")
    if go_viral_cog:
        await go_viral_cog.go_viral_on_ready()
    else:
        print("ERROR: GoViralCog no encontrado. El mensaje de bienvenida no se gestionará.")

    await bot.change_presence(activity=discord.Game(name="Monitoreando el Go-Viral"))


# Cargar cogs (extensiones)
async def load_cogs():
    # Solo cargamos los módulos que son cogs reales con una función setup()
    await bot.load_extension("canales.go_viral")
    # await bot.load_extension("canales.logs")   <-- Esta línea está comentada/eliminada
    # await bot.load_extension("canales.faltas") <-- Esta línea está comentada/eliminada
    await bot.load_extension("canales.presentate") 

    print("All cogs loaded.")

# Ejecutar el bot
if __name__ == "__main__":
    redis_state_instance = RedisState() 
    try:
        redis_state_instance.redis_client.ping()
        print("Conexión a Redis exitosa.")
    except Exception as e:
        print(f"Error al conectar a Redis: {e}")

    bot.run(BOT_TOKEN)
