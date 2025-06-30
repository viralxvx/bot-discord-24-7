import discord
from discord.ext import commands
from config import TOKEN, INTENTS, PREFIX
from redis_database import connect_redis
from state_management import load_state, save_state
from tasks.clean_inactive import clean_inactive_conversations
from tasks.limpiar_expulsados import limpiar_mensajes_expulsados
from tasks.reset_faltas import resetear_faltas_diarias
from tasks.verificar_inactividad import verificar_inactividad
from events import on_ready, on_member, on_message
from commands import permisos

# Iniciar bot
bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS)

# Cargar eventos
bot.event(on_ready.on_ready(bot))
bot.event(on_member.on_member_join(bot))
bot.event(on_message.on_message(bot))

# Cargar comandos
bot.add_command(permisos.permiso)

# Cargar tareas programadas
verificar_inactividad.start(bot)
resetear_faltas_diarias.start(bot)
clean_inactive_conversations.start(bot)
limpiar_mensajes_expulsados.start(bot)

# Iniciar conexión Redis y cargar estado
connect_redis()
load_state()

# Ejecutar bot
bot.run(TOKEN)
