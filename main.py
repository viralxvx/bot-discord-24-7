import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, CANAL_LOGS, CANAL_OBJETIVO # Asegúrate de importar CANAL_OBJETIVO
from canales.logs import registrar_log # Importa tu función de logs
from state_management import RedisState # Necesitas esto para el estado del mensaje de bienvenida

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f'Bot conectado como {bot.user}')

    # --- Cargar la Cog (extensión) aquí ---
    try:
        await bot.load_extension("canales.go_viral") # Esto llamará a async def setup(bot) en go_viral.py
        print("Módulo 'canales.go_viral' cargado como extensión exitosamente.")
    except commands.ExtensionAlreadyLoaded:
        print("Módulo 'canales.go_viral' ya estaba cargado.")
    except commands.ExtensionNotFound:
        print("ERROR: Módulo 'canales.go_viral' no encontrado. Verifica la ruta.")
    except Exception as e:
        print(f"ERROR al cargar la extensión 'canales.go_viral': {e}")


    # --- Lógica de envío al canal de logs ---
    canal_logs = bot.get_channel(CANAL_LOGS)
    if canal_logs:
        try:
            await canal_logs.send(f"🟢 **Bot conectado como `{bot.user.name}` y listo para funcionar.**")
            print("Mensaje de conexión enviado al canal de logs desde main.py.")
        except Exception as e:
            print(f"Error al enviar mensaje al canal de logs desde main.py: {e}")
    else:
        print(f"Error: Canal de logs con ID {CANAL_LOGS} no encontrado en main.py.")

    # --- Llama a la función de inicio específica del Cog ---
    go_viral_cog = bot.get_cog("GoViralCog")
    if go_viral_cog:
        print("Iniciando funciones on_ready específicas de los módulos...")
        await go_viral_cog.go_viral_on_ready()
    else:
        print("ERROR: No se pudo obtener la Cog 'GoViralCog'. ¿Fue cargada correctamente?")


async def main():
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
