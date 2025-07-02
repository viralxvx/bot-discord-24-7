import discord
from discord.ext import commands
import os
import asyncio
from state_management import RedisState
from canales.go_viral import GoViralCog
from canales.logs import registrar_log # Asegúrate de que esta importación esté aquí

# --- Configuración del Bot ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
REDIS_URL = os.getenv('REDIS_URL')
GUILD_ID = os.getenv('GUILD_ID') # Asegúrate de que esta variable de entorno esté configurada

intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Necesario para eventos de miembros, como on_member_join
intents.reactions = True # Necesario para eventos de reacciones

bot = commands.Bot(command_prefix='!', intents=intents)

# --- Evento on_ready ---
@bot.event
async def on_ready():
    print(f'🟢Bot conectado como {bot.user} (ID: {bot.user.id})')
    print('------')

    # ¡AÑADE ESTA LÍNEA AQUÍ PARA REGISTRAR LA CONEXIÓN EN EL CANAL DE LOGS!
    await registrar_log(f"El bot se ha conectado y está en línea.", bot.user, None, bot) 

    # 1. Conectar a Redis y adjuntarlo al bot
    try:
        bot.redis_state = RedisState(REDIS_URL)
        print("Conexión a Redis establecida y adjuntada al bot.")
    except Exception as e:
        print(f"ERROR al conectar a Redis: {e}")
        await registrar_log(f"ERROR al conectar a Redis: {e}", bot.user, None, bot)
        # Considera si quieres que el bot se detenga aquí o continúe sin Redis
        # Por ahora, el bot continuará, pero las funciones que dependan de Redis fallarán.

    # 2. Cargar Cogs
    try:
        # Cargar el cog de GoViral
        await bot.add_cog(GoViralCog(bot))
        print("Cog 'canales.go_viral' cargado.")
    except Exception as e:
        print(f"ERROR al cargar o inicializar cogs: {e}")
        await registrar_log(f"ERROR al cargar o inicializar cogs: {e}", bot.user, None, bot)

    # Lógica para sincronizar comandos de barra (slash commands)
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_commands()
            await bot.tree.sync(guild=guild)
            print(f"Comandos de barra sincronizados para el gremio {GUILD_ID}.")
        else:
            print("GUILD_ID no configurado. Los comandos de barra globales no se sincronizarán con un gremio específico.")
            await bot.tree.sync() # Sincronizar globalmente si no hay GUILD_ID
            print("Comandos de barra globales sincronizados.")
    except Exception as e:
        print(f"ERROR al sincronizar comandos de barra: {e}")
        await registrar_log(f"ERROR al sincronizar comandos de barra: {e}", bot.user, None, bot)


# --- Evento on_message (ejemplo, puedes añadir más lógica aquí) ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return # Ignorar mensajes del propio bot

    # Procesar comandos del bot
    await bot.process_commands(message)

# --- Ejecutar el Bot ---
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    # Asegurarse de que el TOKEN y REDIS_URL estén configurados
    if TOKEN is None:
        print("Error: La variable de entorno DISCORD_BOT_TOKEN no está configurada.")
        exit(1)
    if REDIS_URL is None:
        print("Error: La variable de entorno REDIS_URL no está configurada.")
        exit(1)

    asyncio.run(main())
