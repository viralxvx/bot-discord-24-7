import logging
import sys
from discord_bot import bot
from config import TOKEN

# Importar funciones específicas en lugar de módulos
from events.on_ready import handle_on_ready
from events.on_member import handle_member_join, handle_member_remove
from events.on_message import handle_on_message

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Registrar eventos
@bot.event
async def on_ready():
    await handle_on_ready(bot)

@bot.event
async def on_member_join(member):
    await handle_member_join(member)

@bot.event
async def on_member_remove(member):
    await handle_member_remove(member)

@bot.event
async def on_message(message):
    await handle_on_message(bot, message)

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f"Error en evento {event}: {sys.exc_info()[1]}")

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logging.critical(f"Error al iniciar bot: {str(e)}")
        sys.exit(1)
