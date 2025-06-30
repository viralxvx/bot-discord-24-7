import discord
from discord.ext import commands
import asyncio

from config import TOKEN
from events.on_ready import on_ready
from events.on_member import on_member_join, on_member_remove
from events.on_message import on_message
from utils import save_state  # si usas utils para guardar estado

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # necesario para leer mensajes

bot = commands.Bot(command_prefix="!", intents=intents)

# Registrar eventos
bot.event(on_ready)
bot.event(on_member_join)
bot.event(on_member_remove)
bot.event(on_message)

# Evento para limpiar al cerrar (opcional)
import atexit
atexit.register(save_state)

# Ejecutar el bot
bot.run(TOKEN)
