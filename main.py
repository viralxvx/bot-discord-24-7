from .config import bot, engine, Session
from .models import Base
from .discord_bot import *
from .commands import *
from .tasks import *
from .views import *
from .message_handlers import *
from .app import keep_alive

# Crear tablas si no existen
Base.metadata.create_all(engine)

# Cargar el estado al iniciar y luego iniciar el bot
load_state()
keep_alive()
bot.run(TOKEN)
