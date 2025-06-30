import discord
from discord.ext import commands, tasks
import asyncio
import datetime
from config import TOKEN, PREFIX, ADMIN_ID, CANAL_OBJETIVO, CANAL_REPORTES, CANAL_SOPORTE, CANAL_FALTAS, CANAL_LOGS, CANAL_NORMAS_GENERALES, CANAL_ANUNCIOS, CANAL_X_NORMAS
from redis_database import load_state, save_state, permisos_inactividad, faltas_dict, amonestaciones, baneos_temporales, ultima_publicacion_dict, active_conversations, mensajes_recientes
from handlers import anuncios, faltas, go_viral, logs, normas_generales, presentate, reporte_incumplimiento, soporte, x_normas
from events import on_ready_event, on_member_event, on_message_event
from commands import permisos
from tasks import clean_inactive, limpiar_expulsados, reset_faltas, verificar_inactividad
from utils import add_log, registrar_log, publicar_mensaje_unico
from flask import Flask, jsonify
from threading import Thread
import atexit

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Variables globales cargadas de redis o por defecto
load_state()

# Registro comandos
bot.add_command(permisos.permiso)

# Registro eventos
bot.event(on_ready_event.on_ready)
bot.event(on_member_event.on_member_join)
bot.event(on_message_event.on_message)
bot.event(on_message_event.on_reaction_add)
bot.event(on_member_event.on_member_remove)

# Tareas programadas
verificar_inactividad.verificar_inactividad.start()
clean_inactive.clean_inactive_conversations.start()
limpiar_expulsados.limpiar_mensajes_expulsados.start()
reset_faltas.resetear_faltas_diarias.start()

# Flask para keep_alive
app = Flask('')

@app.route('/')
def home():
    return "El bot está corriendo!"

@app.route('/health')
def health():
    return jsonify({
        "status": "running",
        "bot_ready": bot.is_ready(),
        "last_ready": datetime.datetime.utcnow().isoformat()
    })

def run_webserver():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_webserver)
    t.daemon = True
    t.start()

atexit.register(save_state)

keep_alive()

bot.run(TOKEN)
