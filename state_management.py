import os
import json
import datetime
import redis
import asyncio
import logging
from collections import defaultdict
from config import STATE_FILE

# Variables globales para el estado
ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
amonestaciones = defaultdict(list)
baneos_temporales = defaultdict(lambda: None)
permisos_inactividad = defaultdict(lambda: None)
ticket_counter = 0
active_conversations = {}
faq_data = {}
faltas_dict = defaultdict(lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None})
mensajes_recientes = defaultdict(list)

# Conexión a Redis
redis_client = None

async def init_db():
    global redis_client
    max_retries = 5
    retry_delay = 5  # segundos
    for attempt in range(max_retries):
        try:
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                raise ValueError("REDIS_URL no está configurado en las variables de entorno")
            
            redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            redis_client.ping()
            logging.info(f"Conexión a Redis establecida correctamente (intento {attempt + 1})")
            return
        except Exception as e:
            logging.error(f"Intento {attempt + 1}/{max_retries} de conexión a Redis falló: {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"Reintentando en {retry_delay} segundos...")
                await asyncio.sleep(retry_delay)
            else:
                logging.error("No se pudo conectar a Redis después de varios intentos")
                raise

async def load_state():
    global ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, ticket_counter, active_conversations, faq_data, faltas_dict, mensajes_recientes
    try:
        ultima_publicacion = redis_client.hgetall("ultima_publicacion")
        ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
        for user_id, timestamp in ultima_publicacion.items():
            ultima_publicacion_dict[user_id] = datetime.datetime.fromisoformat(timestamp)

        amonestaciones.clear()
        for user_id in redis_client.smembers("amonestaciones_users"):
            timestamps = redis_client.lrange(f"amonestaciones:{user_id}", 0, -1)
            amonestaciones[user_id] = [datetime.datetime.fromisoformat(ts) for ts in timestamps]

        baneos_temporales.clear()
        baneos = redis_client.hgetall("baneos_temporales")
        for user_id, timestamp in baneos.items():
            if timestamp:
                baneos_temporales[user_id] = datetime.datetime.fromisoformat(timestamp)

        permisos_inactividad.clear()
        permisos = redis_client.hgetall("permisos_inactividad")
        for user_id, data in permisos.items():
            if data:
                permisos_inactividad[user_id] = json.loads(data)

        ticket_counter_value = redis_client.get("ticket_counter")
        global ticket_counter
        ticket_counter = int(ticket_counter_value) if ticket_counter_value else 0

        active_conversations.clear()
        conversations = redis_client.hgetall("active_conversations")
        for user_id, data in conversations.items():
            active_conversations[user_id] = json.loads(data)

        faq_data.clear()
        faq = redis_client.hgetall("faq_data")
        for question, response in faq.items():
            faq_data[question] = response

        faltas_dict.clear()
        faltas = redis_client.hgetall("faltas_dict")
        for user_id, data in faltas.items():
            faltas_dict[user_id] = json.loads(data)

        mensajes_recientes.clear()
        mensajes = redis_client.hgetall("mensajes_recientes")
        for channel_id, messages in mensajes.items():
            mensajes_recientes[channel_id] = json.loads(messages)

        logging.info("Estado cargado desde Redis correctamente")
    except Exception as e:
        logging.error(f"Error al cargar estado desde Redis: {str(e)}")
        raise

async def save_state():
    try:
        redis_client.delete("ultima_publicacion")
        for user_id, timestamp in ultima_publicacion_dict.items():
            redis_client.hset("ultima_publicacion", user_id, timestamp.isoformat())

        redis_client.delete("amonestaciones_users")
        for user_id, timestamps in amonestaciones.items():
            redis_client.sadd("amonestaciones_users", user_id)
            redis_client.delete(f"amonestaciones:{user_id}")
            for timestamp in timestamps:
                redis_client.rpush(f"amonestaciones:{user_id}", timestamp.isoformat())

        redis_client.delete("baneos_temporales")
        for user_id, timestamp in baneos_temporales.items():
            if timestamp:
                redis_client.hset("baneos_temporales", user_id, timestamp.isoformat())

        redis_client.delete("permisos_inactividad")
        for user_id, data in permisos_inactividad.items():
            if data:
                redis_client.hset("permisos_inactividad", user_id, json.dumps(data))

        redis_client.set("ticket_counter", ticket_counter)

        redis_client.delete("active_conversations")
        for user_id, data in active_conversations.items():
            redis_client.hset("active_conversations", user_id, json.dumps(data))

        redis_client.delete("faq_data")
        for question, response in faq_data.items():
            redis_client.hset("faq_data", question, response)

        redis_client.delete("faltas_dict")
        for user_id, data in faltas_dict.items():
            redis_client.hset("faltas_dict", user_id, json.dumps(data))

        redis_client.delete("mensajes_recientes")
        for channel_id, messages in mensajes_recientes.items():
            redis_client.hset("mensajes_recientes", channel_id, json.dumps(messages))

        logging.info("Estado guardado en Redis correctamente")
    except Exception as e:
        logging.error(f"Error al guardar estado en Redis: {str(e)}")
        raise
