import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, CANAL_LOGS, CANAL_OBJETIVO # Asegúrate de importar CANAL_OBJETIVO
from canales.go_viral import setup as go_viral_setup # Importamos la función setup de go_viral
from canales.logs import registrar_log # Importa tu función de logs
from state_management import RedisState # Necesitas esto para el estado del mensaje de bienvenida


intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# La función setup de go_viral.py añade la Cog. No la necesitamos llamar aquí con await si el setup de go_viral.py usa bot.add_cog
# Lo haremos de forma diferente para que se cargue correctamente como una extensión
# En lugar de llamar go_viral_setup(bot) directamente aquí, cargaremos la extensión en on_ready.

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f'Bot conectado como {bot.user}')

    # --- Cargar la Cog (extensión) aquí ---
    try:
        # Asegúrate de que 'canales.go_viral' sea la ruta correcta a tu archivo go_viral.py
        # relative to your main.py. Si main.py y la carpeta canales están al mismo nivel, está bien.
        await bot.load_extension("canales.go_viral")
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
    # Después de cargar la extensión, el Cog ya debería estar disponible
    go_viral_cog = bot.get_cog("GoViralCog") # Obtener la instancia del Cog por su nombre
    if go_viral_cog:
        print("Iniciando funciones on_ready específicas de los módulos...")
        await go_viral_cog.go_viral_on_ready() # Llamar al método específico de la Cog
    else:
        print("ERROR: No se pudo obtener la Cog 'GoViralCog'. ¿Fue cargada correctamente?")


async def main():
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
