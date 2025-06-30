import sys
import os
from threading import Thread

# Añadir el directorio actual al path para permitir importaciones absolutas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
import discord
import re
import datetime
import json
import asyncio
import threading
from discord.ext import commands, tasks
from collections import defaultdict
from discord.ui import View, Select
from discord import SelectOption, Interaction
import atexit

from config import TOKEN, CANAL_OBJETIVO, CANAL_LOGS, CANAL_REPORTES, CANAL_SOPORTE, CANAL_FLUJO_SOPORTE, CANAL_ANUNCIOS, CANAL_NORMAS_GENERALES, CANAL_X_NORMAS, CANAL_FALTAS, ADMIN_ID, INACTIVITY_TIMEOUT, MAX_MENSAJES_RECIENTES, MAX_LOG_LENGTH, LOG_BATCH_DELAY
from discord_bot import bot, on_ready, on_member_remove
from commands import permiso
from tasks import verificar_inactividad, resetear_faltas_diarias, clean_inactive_conversations, limpiar_mensajes_expulsados
from views import ReportMenu, SupportMenu
from message_handlers import on_message, on_reaction_add
from utils import MENSAJE_NORMAS, MENSAJE_ANUNCIO_PERMISOS, MENSAJE_ACTUALIZACION_SISTEMA, FAQ_FALLBACK, calcular_calificacion, actualizar_mensaje_faltas, registrar_log, batch_log, publicar_mensaje_unico
from app import app, run_webserver, keep_alive
from state_management import ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, ticket_counter, active_conversations, faq_data, faltas_dict, mensajes_recientes, save_state

# Estado persistente
STATE_FILE = "state.json"
try:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    
    # Función para cargar datetime con UTC si es naive
    def load_datetime(dt_str):
        if dt_str is None:
            return None
        dt = datetime.datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    
    ultima_publicacion_dict.clear()
    ultima_publicacion_dict.update({k: load_datetime(v) for k, v in state.get("ultima_publicacion_dict", {}).items()})
    
    amonestaciones.clear()
    amonestaciones.update({k: [load_datetime(t) for t in v] for k, v in state.get("amonestaciones", {}).items()})
    
    baneos_temporales.clear()
    baneos_temporales.update({k: load_datetime(v) for k, v in state.get("baneos_temporales", {}).items()})
    
    permisos_inactividad.clear()
    permisos_inactividad.update({k: {"inicio": load_datetime(v["inicio"]), "duracion": v["duracion"]} if v else None 
                               for k, v in state.get("permisos_inactividad", {}).items()})
    
    ticket_counter = state.get("ticket_counter", 0)
    active_conversations = state.get("active_conversations", {})
    faq_data = state.get("faq_data", {})
    
    faltas_dict.clear()
    faltas_dict.update({
        k: {
            "faltas": v["faltas"],
            "aciertos": v["aciertos"],
            "estado": v["estado"],
            "mensaje_id": v["mensaje_id"],
            "ultima_falta_time": load_datetime(v["ultima_falta_time"]) if v["ultima_falta_time"] else None
        } for k, v in state.get("faltas_dict", {}).items()
    })
    
    mensajes_recientes.clear()
    mensajes_recientes.update(state.get("mensajes_recientes", {}))
except FileNotFoundError:
    ultima_publicacion_dict.default_factory = lambda: datetime.datetime.now(datetime.timezone.utc)
    amonestaciones.default_factory = list
    baneos_temporales.default_factory = lambda: None
    permisos_inactividad.default_factory = lambda: None
    ticket_counter = 0
    active_conversations = {}
    faq_data = {}
    faltas_dict.default_factory = lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
    mensajes_recientes.default_factory = list

atexit.register(save_state)

# Iniciar el servidor web en un hilo separado
keep_alive()

# Iniciar el bot
bot.run(TOKEN)
