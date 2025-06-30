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
            
            logging.info(f"Intentando conectar a Redis con URL: {redis_url}")
            redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            response = redis_client.ping()
            logging.info(f"Conexión a Redis establecida correctamente (intento {attempt + 1}, respuesta: {response})")
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
        logging.info("Iniciando carga de estado desde Redis...")
        
        # Cargar ultima_publicacion_dict
        logging.info("Cargando ultima_publicacion...")
        ultima_publicacion = redis_client.hgetall("ultima_publicacion")
        ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
        for user_id, timestamp in ultima_publicacion.items():
            try:
                ultima_publicacion_dict[user_id] = datetime.datetime.fromisoformat(timestamp)
            except ValueError as e:
                logging.error(f"Error al parsear timestamp en ultima_publicacion para user_id {user_id}: {timestamp}, error: {str(e)}")
        logging.info(f"Cargadas {len(ultima_publicacion)} entradas de ultima_publicacion")

        # Cargar amonestaciones
        logging.info("Cargando amonestaciones...")
        amonestaciones.clear()
        amonestaciones_users = redis_client.smembers("amonestaciones_users")
        for user_id in amonestaciones_users:
            timestamps = redis_client.lrange(f"amonestaciones:{user_id}", 0, -1)
            amonestaciones[user_id] = []
            for ts in timestamps:
                try:
                    amonestaciones[user_id].append(datetime.datetime.fromisoformat(ts))
                except ValueError as e:
                    logging.error(f"Error al parsear timestamp en amonestaciones para user_id {user_id}: {ts}, error: {str(e)}")
        logging.info(f"Cargadas amonestaciones para {len(amonestaciones_users)} usuarios")

        # Cargar baneos_temporales
        logging.info("Cargando baneos_temporales...")
        baneos_temporales.clear()
        baneos = redis_client.hgetall("baneos_temporales")
        for user_id, timestamp in baneos.items():
            try:
                if timestamp:
                    baneos_temporales[user_id] = datetime.datetime.fromisoformat(timestamp)
            except ValueError as e:
                logging.error(f"Error al parsear timestamp en baneos_temporales para user_id {user_id}: {timestamp}, error: {str(e)}")
        logging.info(f"Cargadas {len(baneos)} entradas de baneos_temporales")

        # Cargar permisos_inactividad
        logging.info("Cargando permisos_inactividad...")
        permisos_inactividad.clear()
        permisos = redis_client.hgetall("permisos_inactividad")
        for user_id, data in permisos.items():
            try:
                if data:
                    permisos_inactividad[user_id] = json.loads(data)
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear JSON en permisos_inactividad para user_id {user_id}: {data}, error: {str(e)}")
        logging.info(f"Cargadas {len(permisos)} entradas de permisos_inactividad")

        # Cargar ticket_counter
        logging.info("Cargando ticket_counter...")
        ticket_counter_value = redis_client.get("ticket_counter")
        global ticket_counter
        ticket_counter = int(ticket_counter_value) if ticket_counter_value else 0
        logging.info(f"ticket_counter cargado: {ticket_counter}")

        # Cargar active_conversations
        logging.info("Cargando active_conversations...")
        active_conversations.clear()
        conversations = redis_client.hgetall("active_conversations")
        for user_id, data in conversations.items():
            try:
                active_conversations[user_id] = json.loads(data)
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear JSON en active_conversations para user_id {user_id}: {data}, error: {str(e)}")
        logging.info(f"Cargadas {len(conversations)} entradas de active_conversations")

        # Cargar faq_data
        logging.info("Cargando faq_data...")
        faq_data.clear()
        faq = redis_client.hgetall("faq_data")
        for question, response in faq.items():
            faq_data[question] = response
        logging.info(f"Cargadas {len(faq)} entradas de faq_data")

        # Cargar faltas_dict
        logging.info("Cargando faltas_dict...")
        faltas_dict.clear()
        faltas = redis_client.hgetall("faltas_dict")
        for user_id, data in faltas.items():
            try:
                faltas_dict[user_id] = json.loads(data)
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear JSON en faltas_dict para user_id {user_id}: {data}, error: {str(e)}")
        logging.info(f"Cargadas {len(faltas)} entradas de faltas_dict")

        # Cargar mensajes_recientes
        logging.info("Cargando mensajes_recientes...")
        mensajes_recientes.clear()
        mensajes = redis_client.hgetall("mensajes_recientes")
        for channel_id, messages in mensajes.items():
            try:
                mensajes_recientes[channel_id] = json.loads(messages)
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear JSON en mensajes_recientes para channel_id {channel_id}: {messages}, error: {str(e)}")
        logging.info(f"Cargadas {len(mensajes)} entradas de mensajes_recientes")

        logging.info("Estado cargado desde Redis correctamente")
    except Exception as e:
        logging.error(f"Error al cargar estado desde Redis: {str(e)}")
        logging.error(traceback.format_exc())
        raise

async def save_state():
    try:
        logging.info("Iniciando guardado de estado en Redis...")
        
        # Guardar ultima_publicacion_dict
        logging.info("Guardando ultima_publicacion...")
        redis_client.delete("ultima_publicacion")
        for user_id, timestamp in ultima_publicacion_dict.items():
            redis_client.hset("ultima_publicacion", user_id, timestamp.isoformat())
        logging.info(f"Guardadas {len(ultima_publicacion_dict)} entradas en ultima_publicacion")

        # Guardar amonestaciones
        logging.info("Guardando amonestaciones...")
        redis_client.delete("amonestaciones_users")
        for user_id, timestamps in amonestaciones.items():
            redis_client.sadd("amonestaciones_users", user_id)
            redis_client.delete(f"amonestaciones:{user_id}")
            for timestamp in timestamps:
                redis_client.rpush(f"amonestaciones:{user_id}", timestamp.isoformat())
        logging.info(f"Guardadas amonestaciones para {len(amonestaciones)} usuarios")

        # Guardar baneos_temporales
        logging.info("Guardando baneos_temporales...")
        redis_client.delete("baneos_temporales")
        for user_id, timestamp in baneos_temporales.items():
            if timestamp:
                redis_client.hset("baneos_temporales", user_id, timestamp.isoformat())
        logging.info(f"Guardadas {len(baneos_temporales)} entradas en baneos_temporales")

        # Guardar permisos_inactividad
        logging.info("Guardando permisos_inactividad...")
        redis_client.delete("permisos_inactividad")
        for user_id, data in permisos_inactividad.items():
            if data:
                redis_client.hset("permisos_inactividad", user_id, json.dumps(data))
        logging.info(f"Guardadas {len(permisos_inactividad)} entradas en permisos_inactividad")

        # Guardar ticket_counter
        logging.info("Guardando ticket_counter...")
        redis_client.set("ticket_counter", ticket_counter)
        logging.info(f"ticket_counter guardado: {ticket_counter}")

        # Guardar active_conversations
        logging.info("Guardando active_conversations...")
        redis_client.delete("active_conversations")
        for user_id, data in active_conversations.items():
            redis_client.hset("active_conversations", user_id, json.dumps(data))
        logging.info(f"Guardadas {len(active_conversations)} entradas en active_conversations")

        # Guardar faq_data
        logging.info("Guardando faq_data...")
        redis_client.delete("faq_data")
        for question, response in faq_data.items():
            redis_client.hset("faq_data", question, response)
        logging.info(f"Guardadas {len(faq_data)} entradas en faq_data")

        # Guardar faltas_dict
        logging.info("Guardando faltas_dict...")
        redis_client.delete("faltas_dict")
        for user_id, data in faltas_dict.items():
            redis_client.hset("faltas_dict", user_id, json.dumps(data))
        logging.info(f"Guardadas {len(faltas_dict)} entradas en faltas_dict")

        # Guardar mensajes_recientes
        logging.info("Guardando mensajes_recientes...")
        redis_client.delete("mensajes_recientes")
        for channel_id, messages in mensajes_recientes.items():
            redis_client.hset("mensajes_recientes", channel_id, json.dumps(messages))
        logging.info(f"Guardadas {len(mensajes_recientes)} entradas en mensajes_recientes")

        logging.info("Estado guardado en Redis correctamente")
    except Exception as e:
        logging.error(f"Error al guardar estado en Redis: {str(e)}")
        logging.error(traceback.format_exc())
        raise
