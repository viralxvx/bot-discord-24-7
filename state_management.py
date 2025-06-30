import os
import json
import datetime
import asyncpg
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

# Conexión a PostgreSQL
pool = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    async with pool.acquire() as conn:
        # Crear tablas si no existen
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS ultima_publicacion (
                user_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS amonestaciones (
                user_id TEXT,
                timestamp TIMESTAMP WITH TIME ZONE,
                PRIMARY KEY (user_id, timestamp)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS baneos_temporales (
                user_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS permisos_inactividad (
                user_id TEXT PRIMARY KEY,
                inicio TIMESTAMP WITH TIME ZONE,
                duracion INTEGER
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS ticket_counter (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS active_conversations (
                user_id TEXT PRIMARY KEY,
                message_ids JSONB,
                last_time TIMESTAMP WITH TIME ZONE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS faq_data (
                question TEXT PRIMARY KEY,
                response TEXT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS faltas_dict (
                user_id TEXT PRIMARY KEY,
                faltas INTEGER,
                aciertos INTEGER,
                estado TEXT,
                mensaje_id TEXT,
                ultima_falta_time TIMESTAMP WITH TIME ZONE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS mensajes_recientes (
                channel_id TEXT PRIMARY KEY,
                messages JSONB
            )
        ''')

async def load_state():
    global ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, ticket_counter, active_conversations, faq_data, faltas_dict, mensajes_recientes
    async with pool.acquire() as conn:
        # Cargar ultima_publicacion_dict
        records = await conn.fetch('SELECT user_id, timestamp FROM ultima_publicacion')
        ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
        for record in records:
            ultima_publicacion_dict[record['user_id']] = record['timestamp']

        # Cargar amonestaciones
        amonestaciones.clear()
        records = await conn.fetch('SELECT user_id, timestamp FROM amonestaciones')
        for record in records:
            amonestaciones[record['user_id']].append(record['timestamp'])

        # Cargar baneos_temporales
        baneos_temporales.clear()
        records = await conn.fetch('SELECT user_id, timestamp FROM baneos_temporales')
        for record in records:
            baneos_temporales[record['user_id']] = record['timestamp']

        # Cargar permisos_inactividad
        permisos_inactividad.clear()
        records = await conn.fetch('SELECT user_id, inicio, duracion FROM permisos_inactividad')
        for record in records:
            permisos_inactividad[record['user_id']] = {"inicio": record['inicio'], "duracion": record['duracion']}

        # Cargar ticket_counter
        record = await conn.fetchrow('SELECT value FROM ticket_counter WHERE id = 1')
        global ticket_counter
        ticket_counter = record['value'] if record else 0

        # Cargar active_conversations
        active_conversations.clear()
        records = await conn.fetch('SELECT user_id, message_ids, last_time FROM active_conversations')
        for record in records:
            active_conversations[record['user_id']] = {
                "message_ids": record['message_ids'],
                "last_time": record['last_time']
            }

        # Cargar faq_data
        faq_data.clear()
        records = await conn.fetch('SELECT question, response FROM faq_data')
        for record in records:
            faq_data[record['question']] = record['response']

        # Cargar faltas_dict
        faltas_dict.clear()
        records = await conn.fetch('SELECT user_id, faltas, aciertos, estado, mensaje_id, ultima_falta_time FROM faltas_dict')
        for record in records:
            faltas_dict[record['user_id']] = {
                "faltas": record['faltas'],
                "aciertos": record['aciertos'],
                "estado": record['estado'],
                "mensaje_id": record['mensaje_id'],
                "ultima_falta_time": record['ultima_falta_time']
            }

        # Cargar mensajes_recientes
        mensajes_recientes.clear()
        records = await conn.fetch('SELECT channel_id, messages FROM mensajes_recientes')
        for record in records:
            mensajes_recientes[record['channel_id']] = record['messages']

async def save_state():
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Guardar ultima_publicacion_dict
            await conn.execute('DELETE FROM ultima_publicacion')
            for user_id, timestamp in ultima_publicacion_dict.items():
                await conn.execute(
                    'INSERT INTO ultima_publicacion (user_id, timestamp) VALUES ($1, $2)',
                    str(user_id), timestamp
                )

            # Guardar amonestaciones
            await conn.execute('DELETE FROM amonestaciones')
            for user_id, timestamps in amonestaciones.items():
                for timestamp in timestamps:
                    await conn.execute(
                        'INSERT INTO amonestaciones (user_id, timestamp) VALUES ($1, $2)',
                        str(user_id), timestamp
                    )

            # Guardar baneos_temporales
            await conn.execute('DELETE FROM baneos_temporales')
            for user_id, timestamp in baneos_temporales.items():
                if timestamp:
                    await conn.execute(
                        'INSERT INTO baneos_temporales (user_id, timestamp) VALUES ($1, $2)',
                        str(user_id), timestamp
                    )

            # Guardar permisos_inactividad
            await conn.execute('DELETE FROM permisos_inactividad')
            for user_id, data in permisos_inactividad.items():
                if data:
                    await conn.execute(
                        'INSERT INTO permisos_inactividad (user_id, inicio, duracion) VALUES ($1, $2, $3)',
                        str(user_id), data["inicio"], data["duracion"]
                    )

            # Guardar ticket_counter
            await conn.execute(
                'INSERT INTO ticket_counter (id, value) VALUES (1, $1) ON CONFLICT (id) DO UPDATE SET value = $1',
                ticket_counter
            )

            # Guardar active_conversations
            await conn.execute('DELETE FROM active_conversations')
            for user_id, data in active_conversations.items():
                await conn.execute(
                    'INSERT INTO active_conversations (user_id, message_ids, last_time) VALUES ($1, $2, $3)',
                    str(user_id), data["message_ids"], data["last_time"]
                )

            # Guardar faq_data
            await conn.execute('DELETE FROM faq_data')
            for question, response in faq_data.items():
                await conn.execute(
                    'INSERT INTO faq_data (question, response) VALUES ($1, $2)',
                    question, response
                )

            # Guardar faltas_dict
            await conn.execute('DELETE FROM faltas_dict')
            for user_id, data in faltas_dict.items():
                await conn.execute(
                    'INSERT INTO faltas_dict (user_id, faltas, aciertos, estado, mensaje_id, ultima_falta_time) VALUES ($1, $2, $3, $4, $5, $6)',
                    str(user_id), data["faltas"], data["aciertos"], data["estado"], data["mensaje_id"], data["ultima_falta_time"]
                )

            # Guardar mensajes_recientes
            await conn.execute('DELETE FROM mensajes_recientes')
            for channel_id, messages in mensajes_recientes.items():
                await conn.execute(
                    'INSERT INTO mensajes_recientes (channel_id, messages) VALUES ($1, $2)',
                    str(channel_id), messages
                )
