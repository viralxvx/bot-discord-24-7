import discord
from discord.ext import commands
import asyncio
import datetime
from config import TOKEN, PREFIX
from tasks import clean_inactive, limpiar_expulsados, reset_faltas, verificar_inactividad
from events import on_member, on_message
from utils import registrar_log  # Si tienes esta función para logs

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Registrar eventos
bot.event(on_member.on_member_join)
bot.event(on_member.on_member_remove)
bot.event(on_message.on_message)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"Hora UTC: {datetime.datetime.utcnow().isoformat()}")

    # Iniciar tareas programadas
    verificar_inactividad.start()
    reset_faltas.start()
    clean_inactive.start()
    limpiar_expulsados.start()

    await registrar_log("🤖 Bot listo y conectado", categoria="sistema")
