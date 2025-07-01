# main.py
import discord
from discord.ext import commands
import os
from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from state_management import RedisState 
from canales.logs import registrar_log # Importamos registrar_log aquí también

# Configuración de intents para el bot
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True         

# Inicializa el bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Mensaje de conexión deseado
    print(f'🟢Bot conectado como {bot.user.name} (ID: {bot.user.id}) y listo para funcionar..')
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
    
    # Registrar en el canal de logs que el bot está en línea
    await registrar_log("Bot se ha conectado y está en línea.", bot.user, None, bot)


@bot.event
async def on_disconnect():
    # Este evento se dispara cuando el bot se desconecta de Discord
    print(f'🔴Bot desconectado. Última conexión: {discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}')
    # Intentar registrar en el canal de logs, aunque la conexión podría estar perdida
    # Es posible que este log no siempre llegue si la desconexión es abrupta
    try:
        await registrar_log("Bot se ha desconectado.", bot.user, None, bot)
    except Exception as e:
        print(f"Error al intentar registrar desconexión en logs: {e}")


# Cargar cogs (extensiones)
async def load_cogs():
    # Solo cargamos los módulos que son cogs reales con una función setup()
    await bot.load_extension("canales.go_viral")
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
