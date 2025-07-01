import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, CANAL_LOGS # Solo necesitas CANAL_LOGS aquí para el mensaje de conexión del bot
from canales.go_viral import setup as go_viral_setup
from canales.logs import registrar_log # Importa tu función de logs

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Registra los eventos de go_viral
go_viral_setup(bot)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f'Bot conectado como {bot.user}')

    # Lógica de envío al canal de logs desde main.py
    canal_logs = bot.get_channel(CANAL_LOGS)
    if canal_logs:
        try:
            await canal_logs.send(f"🟢 **Bot conectado como `{bot.user.name}` y listo para funcionar.**")
            print("Mensaje de conexión enviado al canal de logs desde main.py.")
        except Exception as e:
            print(f"Error al enviar mensaje al canal de logs desde main.py: {e}")
    else:
        print(f"Error: Canal de logs con ID {CANAL_LOGS} no encontrado en main.py.")

    # Después de que el bot esté completamente listo, llama a las funciones de inicio de los módulos
    # Esto asegura que todos los cachés estén listos antes de que los módulos intenten acceder a los canales
    print("Iniciando funciones on_ready específicas de los módulos...")
    # Llama directamente a la función que deseas ejecutar del módulo go_viral
    await bot.get_cog("GoViralCog").go_viral_on_ready() # Suponiendo que lo organizas como una Cog

async def main():
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
