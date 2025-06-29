from flask import Flask
from threading import Thread
import discord
import re
import os
import datetime
import sqlite3
import asyncio
import json
from discord.ext import commands, tasks
from collections import defaultdict
from discord.ui import View, Select
from discord import SelectOption, Interaction

# Flask para mantener el contenedor activo en Railway
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Configuración del bot
TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]
CANAL_LOGS = "📝logs"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "👨🔧soporte"
CANAL_FLUJO_SOPORTE = "flujo-de-soporte"
CANAL_ANUNCIOS = "🔔anuncios"
CANAL_NORMAS_GENERALES = "✅normas-generales"
CANAL_X_NORMAS = "𝕏-normas"
CANAL_FALTAS = "📤faltas"
ADMIN_ID = os.environ.get("ADMIN_ID", "1174775323649392844")
INACTIVITY_TIMEOUT = 300  # 5 minutos en segundos
MAX_MENSAJES_RECIENTES = 10  # Máximo de mensajes recientes por canal

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuración de SQLite
DB_FILE = "/app/bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE, timeout=20)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS ultima_publicacion (
            user_id TEXT PRIMARY KEY,
            ultima_publicacion_time TEXT
        );
        CREATE TABLE IF NOT EXISTS amonestaciones (
            user_id TEXT,
            amonestacion_time TEXT,
            PRIMARY KEY (user_id, amonestacion_time)
        );
        CREATE TABLE IF NOT EXISTS baneos_temporales (
            user_id TEXT PRIMARY KEY,
            baneo_time TEXT
        );
        CREATE TABLE IF NOT EXISTS permisos_inactividad (
            user_id TEXT PRIMARY KEY,
            inicio TEXT,
            duracion INTEGER
        );
        CREATE TABLE IF NOT EXISTS faltas (
            user_id TEXT PRIMARY KEY,
            faltas INTEGER,
            aciertos INTEGER,
            estado TEXT,
            mensaje_id TEXT,
            ultima_falta_time TEXT
        );
        CREATE TABLE IF NOT EXISTS ticket_counter (
            id INTEGER PRIMARY KEY,
            counter INTEGER
        );
        CREATE TABLE IF NOT EXISTS active_conversations (
            user_id TEXT PRIMARY KEY,
            last_time TEXT,
            message_ids TEXT
        );
        CREATE TABLE IF NOT EXISTS faq_data (
            pregunta TEXT PRIMARY KEY,
            respuesta TEXT
        );
        CREATE TABLE IF NOT EXISTS mensajes_recientes (
            canal_id TEXT,
            mensaje TEXT,
            PRIMARY KEY (canal_id, mensaje)
        );
    """)
    conn.commit()
    conn.close()

# Estructuras de datos
ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.utcnow())
amonestaciones = defaultdict(list)
baneos_temporales = defaultdict(lambda: None)
permisos_inactividad = defaultdict(lambda: None)
ticket_counter = 0
active_conversations = {}
faq_data = {}
faltas_dict = defaultdict(lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None})
mensajes_recientes = defaultdict(list)

def load_state():
    conn = sqlite3.connect(DB_FILE, timeout=20)
    cursor = conn.cursor()
    
    global ticket_counter, active_conversations, faq_data
    ultima_publicacion_dict.clear()
    amonestaciones.clear()
    baneos_temporales.clear()
    permisos_inactividad.clear()
    faltas_dict.clear()
    mensajes_recientes.clear()

    cursor.execute("SELECT user_id, ultima_publicacion_time FROM ultima_publicacion")
    for row in cursor.fetchall():
        ultima_publicacion_dict[row[0]] = datetime.datetime.fromisoformat(row[1]) if row[1] else datetime.datetime.utcnow()

    cursor.execute("SELECT user_id, amonestacion_time FROM amonestaciones")
    for row in cursor.fetchall():
        amonestaciones[row[0]].append(datetime.datetime.fromisoformat(row[1]))

    cursor.execute("SELECT user_id, baneo_time FROM baneos_temporales")
    for row in cursor.fetchall():
        baneos_temporales[row[0]] = datetime.datetime.fromisoformat(row[1]) if row[1] else None

    cursor.execute("SELECT user_id, inicio, duracion FROM permisos_inactividad")
    for row in cursor.fetchall():
        permisos_inactividad[row[0]] = {"inicio": datetime.datetime.fromisoformat(row[1]), "duracion": row[2]}

    cursor.execute("SELECT counter FROM ticket_counter WHERE id = 1")
    result = cursor.fetchone()
    ticket_counter = result[0] if result else 0

    cursor.execute("SELECT user_id, last_time, message_ids FROM active_conversations")
    for row in cursor.fetchall():
        active_conversations[row[0]] = {
            "last_time": datetime.datetime.fromisoformat(row[1]) if row[1] else None,
            "message_ids": json.loads(row[2]) if row[2] else []
        }

    cursor.execute("SELECT pregunta, respuesta FROM faq_data")
    for row in cursor.fetchall():
        faq_data[row[0]] = row[1]

    cursor.execute("SELECT user_id, faltas, aciertos, estado, mensaje_id, ultima_falta_time FROM faltas")
    for row in cursor.fetchall():
        faltas_dict[row[0]] = {
            "faltas": row[1],
            "aciertos": row[2],
            "estado": row[3],
            "mensaje_id": row[4],
            "ultima_falta_time": datetime.datetime.fromisoformat(row[5]) if row[5] else None
        }

    cursor.execute("SELECT canal_id, mensaje FROM mensajes_recientes")
    for row in cursor.fetchall():
        mensajes_recientes[row[0]].append(row[1])

    conn.close()

def save_state():
    conn = sqlite3.connect(DB_FILE, timeout=20)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM ultima_publicacion")
    cursor.execute("DELETE FROM amonestaciones")
    cursor.execute("DELETE FROM baneos_temporales")
    cursor.execute("DELETE FROM permisos_inactividad")
    cursor.execute("DELETE FROM ticket_counter")
    cursor.execute("DELETE FROM active_conversations")
    cursor.execute("DELETE FROM faq_data")
    cursor.execute("DELETE FROM faltas")
    cursor.execute("DELETE FROM mensajes_recientes")

    for user_id, time in ultima_publicacion_dict.items():
        cursor.execute("INSERT INTO ultima_publicacion (user_id, ultima_publicacion_time) VALUES (?, ?)",
                      (str(user_id), time.isoformat()))

    for user_id, times in amonestaciones.items():
        for time in times:
            cursor.execute("INSERT INTO amonestaciones (user_id, amonestacion_time) VALUES (?, ?)",
                          (str(user_id), time.isoformat()))

    for user_id, time in baneos_temporales.items():
        cursor.execute("INSERT INTO baneos_temporales (user_id, baneo_time) VALUES (?, ?)",
                      (str(user_id), time.isoformat() if time else None))

    for user_id, data in permisos_inactividad.items():
        if data:
            cursor.execute("INSERT INTO permisos_inactividad (user_id, inicio, duracion) VALUES (?, ?, ?)",
                          (str(user_id), data["inicio"].isoformat(), data["duracion"]))

    cursor.execute("INSERT OR REPLACE INTO ticket_counter (id, counter) VALUES (1, ?)", (ticket_counter,))

    for user_id, data in active_conversations.items():
        cursor.execute("INSERT INTO active_conversations (user_id, last_time, message_ids) VALUES (?, ?, ?)",
                      (str(user_id), data["last_time"].isoformat() if data["last_time"] else None, json.dumps(data["message_ids"])))

    for pregunta, respuesta in faq_data.items():
        cursor.execute("INSERT INTO faq_data (pregunta, respuesta) VALUES (?, ?)", (pregunta, respuesta))

    for user_id, data in faltas_dict.items():
        cursor.execute("INSERT INTO faltas (user_id, faltas, aciertos, estado, mensaje_id, ultima_falta_time) VALUES (?, ?, ?, ?, ?, ?)",
                      (str(user_id), data["faltas"], data["aciertos"], data["estado"], data["mensaje_id"],
                       data["ultima_falta_time"].isoformat() if data["ultima_falta_time"] else None))

    for canal_id, mensajes in mensajes_recientes.items():
        for mensaje in mensajes:
            cursor.execute("INSERT INTO mensajes_recientes (canal_id, mensaje) VALUES (?, ?)", (str(canal_id), mensaje))

    conn.commit()
    conn.close()

# Inicializar base de datos y cargar estado
init_db()
load_state()

# Mensajes y constantes
MENSAJE_NORMAS = (
    "📌 **Bienvenid@ al canal 🧵go-viral**\n\n"
    "🔹 **Reacciona con 🔥** a todas las publicaciones de otros miembros desde tu última publicación antes de volver a publicar.\n"
    "🔹 **Reacciona con 👍** a tu propia publicación.\n"
    "🔹 **Solo se permiten enlaces de X (Twitter)** con este formato:\n"
    "```https://x.com/usuario/status/1234567890123456789```\n"
    "❌ **Publicaciones con texto adicional, formato incorrecto o repetidas** serán eliminadas y contarán como una falta, reduciendo tu calificación en 1%.\n"
    "⏳ **Permisos de inactividad**: Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para pausar la obligación de publicar hasta 7 días. Extiende antes de que expire.\n"
    "🚫 **Mensajes repetidos** serán eliminados en todos los canales (excepto #📝logs) para mantener el servidor limpio."
)

MENSAJE_ANUNCIO_PERMISOS = (
    "🚨 **NUEVA REGLA: Permisos de Inactividad**\n\n"
    "**Ahora puedes solicitar un permiso de inactividad** en #⛔reporte-de-incumplimiento usando el comando `!permiso <días>`:\n"
    "✅ **Máximo 7 días** por permiso.\n"
    "🔄 **Extiende el permiso** con otro reporte antes de que expire, siempre antes de un baneo.\n"
    "📤 **Revisa tu estado** en #📤faltas para mantenerte al día.\n"
    "🚫 **Mensajes repetidos** serán eliminados en todos los canales (excepto #📝logs) para mantener el servidor limpio.\n"
    "¡**Gracias por mantener la comunidad activa y organizada**! 🚀"
)

MENSAJE_ACTUALIZACION_SISTEMA = (
    "🚫 **FALTAS DE LOS USUARIOS**\n\n"
    "**Reglas de Inactividad**:\n"
    "⚠️ Si un usuario pasa **3 días sin publicar** en #🧵go-viral, será **baneado por 7 días** de forma automática.\n"
    "⛔️ Si después del baneo pasa **otros 3 días sin publicar**, el sistema lo **expulsará automáticamente** del servidor.\n\n"
    "**Permisos de Inactividad**:\n"
    "✅ Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para solicitar un permiso de hasta **7 días**.\n"
    "🔄 Puedes **extender el permiso** antes de que expire, siempre antes de un baneo.\n"
    "✅ Estas medidas buscan mantener una **comunidad activa y comprometida**, haciendo que el programa de crecimiento sea más eficiente.\n"
    "📤 **Revisa tu estado** en este canal (#📤faltas) para mantenerte al día con tu participación.\n\n"
    "**Gracias por tu comprensión y compromiso. ¡Sigamos creciendo juntos!** 🚀"
)

FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": "VX es una comunidad donde crecemos apoyándonos. Tú apoyas, y luego te apoyan. Publicas tu post después de apoyar a los demás. 🔥 = apoyaste, 👍 = tu propio post.",
    "✅ ¿Cómo publico mi post?": "Para publicar: 1️⃣ Apoya todos los posts anteriores (like + RT + comentario) 2️⃣ Reacciona con 🔥 en Discord 3️⃣ Luego publica tu post y colócale 👍. No uses 🔥 en tu propio post ni repitas mensajes.",
    "✅ ¿Cómo subo de nivel?": "Subes de nivel participando activamente, apoyando a todos y siendo constante. Los niveles traen beneficios como prioridad, mentoría y más."
}

# Cola de logs para evitar rate limits
log_queue = []

async def registrar_log(texto, categoria="general"):
    global log_queue
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{categoria.upper()}] {texto}"
    
    # Truncar mensaje si excede 1900 caracteres
    if len(log_message) > 1900:
        log_message = log_message[:1897] + "..."
    
    log_queue.append(log_message)
    
    # Enviar logs en lotes
    if len(log_queue) >= 10 or sum(len(msg) for msg in log_queue) >= 1500:
        canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
        if canal_log:
            try:
                mensaje = ""
                messages_to_send = []
                for msg in log_queue:
                    if len(mensaje) + len(msg) + 1 <= 1900:
                        mensaje += msg + "\n"
                    else:
                        messages_to_send.append(mensaje.strip())
                        mensaje = msg + "\n"
                if mensaje:
                    messages_to_send.append(mensaje.strip())
                
                for msg in messages_to_send:
                    if msg:
                        await canal_log.send(msg)
                        await asyncio.sleep(1)
                log_queue.clear()
            except discord.errors.Forbidden:
                print(f"No tengo permisos para enviar logs en #{CANAL_LOGS}: {msg}")
            except discord.errors.HTTPException as e:
                print(f"Error enviando logs: {str(e)}")

async def flush_log_queue():
    global log_queue
    if log_queue:
        canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
        if canal_log:
            try:
                mensaje = ""
                messages_to_send = []
                for msg in log_queue:
                    if len(mensaje) + len(msg) + 1 <= 1900:
                        mensaje += msg + "\n"
                    else:
                        messages_to_send.append(mensaje.strip())
                        mensaje = msg + "\n"
                if mensaje:
                    messages_to_send.append(mensaje.strip())
                
                for msg in messages_to_send:
                    if msg:
                        await canal_log.send(msg)
                        await asyncio.sleep(1)
                log_queue.clear()
            except discord.errors.Forbidden:
                print(f"No tengo permisos para enviar logs en #{CANAL_LOGS}: {msg}")
            except discord.errors.HTTPException as e:
                print(f"Error enviando logs: {str(e)}")

def calcular_calificacion(faltas):
    porcentaje = max(0, 100 - faltas)
    barras = int(porcentaje // 10)
    barra_visual = "[" + "█" * barras + " " * (10 - barras) + "]"
    return porcentaje, f"{barra_visual} {porcentaje:.2f}%"

async def limpiar_mensajes_antiguos(canal_faltas):
    try:
        mensajes_a_eliminar = []
        async for msg in canal_faltas.history(limit=200):
            if msg.author == bot.user and not msg.content.startswith("🚫 **FALTAS DE LOS USUARIOS**"):
                mensajes_a_eliminar.append(msg)
        for msg in mensajes_a_eliminar:
            try:
                await msg.delete()
                await registrar_log(f"🗑️ Mensaje antiguo eliminado en #{CANAL_FALTAS}: {msg.content[:50]}...", categoria="faltas")
                await asyncio.sleep(0.5)
            except discord.errors.Forbidden:
                await registrar_log(f"❌ No tengo permisos para eliminar mensajes en #{CANAL_FALTAS}", categoria="faltas")
        await flush_log_queue()
    except discord.errors.Forbidden:
        await registrar_log(f"❌ No tengo permisos para leer/eliminar mensajes en #{CANAL_FALTAS}", categoria="faltas")

async def actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, estado):
    await asyncio.sleep(1)
    try:
        calificacion, barra_visual = calcular_calificacion(faltas)
        contenido = (
            f"👤 **Usuario**: {miembro.mention}\n"
            f"📊 **Faltas en #🧵go-viral**: {faltas} {'👻' if faltas > 0 else ''}\n"
            f"✅ **Aciertos**: {aciertos}\n"
            f"📈 **Calificación**: {barra_visual}\n"
            f"🚨 **Estado de Inactividad**: {estado}\n"
        )
        mensaje_id = faltas_dict[miembro.id]["mensaje_id"]
        if mensaje_id:
            try:
                mensaje = await canal_faltas.fetch_message(mensaje_id)
                if mensaje.content != contenido:
                    await mensaje.edit(content=contenido)
                    await registrar_log(f"📤 Mensaje actualizado para {miembro.name} en #{CANAL_FALTAS}: Faltas={faltas}, Aciertos={aciertos}, Estado={estado}", categoria="faltas")
                return
            except discord.errors.NotFound:
                await registrar_log(f"❌ Mensaje {mensaje_id} no encontrado para {miembro.name} en #{CANAL_FALTAS}, creando uno nuevo", categoria="faltas")
                faltas_dict[miembro.id]["mensaje_id"] = None
            except discord.errors.Forbidden:
                await registrar_log(f"❌ No tengo permisos para editar mensajes en #{CANAL_FALTAS} para {miembro.name}", categoria="faltas")
        mensaje = await canal_faltas.send(contenido)
        faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
        await registrar_log(f"📤 Mensaje creado para {miembro.name} en #{CANAL_FALTAS}: Faltas={faltas}, Aciertos={aciertos}, Estado={estado}", categoria="faltas")
        save_state()
    except Exception as e:
        await registrar_log(f"❌ Error al actualizar mensaje en #{CANAL_FALTAS} para {miembro.name}: {str(e)}", categoria="faltas")

async def verificar_historial_repetidos():
    admin = bot.get_user(int(ADMIN_ID))
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == CANAL_LOGS:
                continue
            mensajes_vistos = set()
            mensajes_a_eliminar = []
            try:
                async for message in channel.history(limit=100):
                    mensaje_normalizado = message.content.strip().lower()
                    if not mensaje_normalizado:
                        continue
                    if channel.name == CANAL_FALTAS:
                        if message.author == bot.user and mensaje_normalizado.startswith("🚫 faltas de los usuarios"):
                            if mensaje_normalizado in mensajes_vistos:
                                mensajes_a_eliminar.append(message)
                            else:
                                mensajes_vistos.add(mensaje_normalizado)
                        continue
                    if message.author == bot.user and channel.name in [CANAL_ANUNCIOS, CANAL_OBJETIVO, CANAL_NORMAS_GENERALES]:
                        if mensaje_normalizado in mensajes_vistos:
                            mensajes_a_eliminar.append(message)
                        else:
                            mensajes_vistos.add(mensaje_normalizado)
                    elif mensaje_normalizado in mensajes_vistos:
                        mensajes_a_eliminar.append(message)
                    else:
                        mensajes_vistos.add(mensaje_normalizado)
                        canal_id = str(channel.id)
                        mensajes_recientes[canal_id].append(message.content)
                        if len(mensajes_recientes[canal_id]) > MAX_MENSAJES_RECIENTES:
                            mensajes_recientes[canal_id].pop(0)
                for message in mensajes_a_eliminar:
                    try:
                        await message.delete()
                        await registrar_log(f"🗑️ Mensaje repetido eliminado del historial en #{channel.name} por {message.author.name}: {message.content[:50]}...", categoria="repetidos")
                        await asyncio.sleep(0.5)
                        if message.author == bot.user and admin:
                            try:
                                await admin.send(
                                    f"⚠️ **Mensaje del bot eliminado**: Un mensaje repetido del bot en #{channel.name} fue eliminado: {message.content[:50]}..."
                                )
                            except:
                                await registrar_log(f"❌ No se pudo notificar eliminación de mensaje del bot al admin", categoria="repetidos")
                        elif message.author != bot.user:
                            try:
                                await message.author.send(
                                    f"⚠️ **Mensaje repetido eliminado**: Un mensaje repetido tuyo en #{channel.name} fue eliminado del historial para mantener el servidor limpio."
                                )
                            except:
                                await registrar_log(f"❌ No se pudo notificar eliminación de mensaje repetido a {message.author.name}", categoria="repetidos")
                    except discord.Forbidden:
                        await registrar_log(f"❌ No tengo permisos para eliminar mensajes en #{channel.name}", categoria="repetidos")
                save_state()
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para leer el historial en #{channel.name}", categoria="repetidos")
    await flush_log_queue()

async def publicar_mensaje_unico(canal, contenido, pinned=False):
    await asyncio.sleep(1)
    try:
        contenido_normalizado = contenido.strip().lower()
        mensajes_vistos = set()
        mensajes_a_eliminar = []
        async for msg in canal.history(limit=100):
            msg_normalizado = msg.content.strip().lower()
            if msg.author == bot.user:
                if msg_normalizado == contenido_normalizado or msg_normalizado in mensajes_vistos:
                    mensajes_a_eliminar.append(msg)
                else:
                    mensajes_vistos.add(msg_normalizado)
            if pinned and msg.pinned and msg.author == bot.user:
                mensajes_a_eliminar.append(msg)
        for msg in mensajes_a_eliminar:
            try:
                await msg.delete()
                await registrar_log(f"🗑️ Mensaje del bot eliminado en #{canal.name}: {msg.content[:50]}...", categoria="mensajes")
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para eliminar mensajes en #{canal.name}", categoria="mensajes")
        mensaje = await canal.send(contenido)
        if pinned:
            await mensaje.pin()
            await registrar_log(f"📌 Mensaje anclado en #{canal.name}: {contenido[:50]}...", categoria="mensajes")
        await registrar_log(f"📢 Mensaje publicado en #{canal.name}: {contenido[:50]}...", categoria="mensajes")
        await flush_log_queue()
        return mensaje
    except discord.Forbidden:
        await registrar_log(f"❌ No tengo permisos para enviar/anclar mensajes en #{canal.name}", categoria="mensajes")
        return None

@bot.event
async def on_ready():
    global ticket_counter, faq_data
    print(f"Bot conectado como {bot.user}")
    await registrar_log(f"Bot iniciado. ADMIN_ID cargado: {ADMIN_ID}", categoria="bot")
    
    await verificar_historial_repetidos()
    
    procesos_exitosos = []
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if canal_faltas:
        try:
            # Eliminar mensajes antiguos del bot en #📤faltas
            await limpiar_mensajes_antiguos(canal_faltas)
            procesos_exitosos.append("Limpieza de mensajes antiguos en #📤faltas")
            
            # Publicar o actualizar mensaje del sistema
            mensaje_sistema = None
            async for msg in canal_faltas.history(limit=100):
                if msg.author == bot.user and msg.content.startswith("🚫 **FALTAS DE LOS USUARIOS**"):
                    mensaje_sistema = msg
                    break
            if mensaje_sistema:
                if mensaje_sistema.content != MENSAJE_ACTUALIZACION_SISTEMA:
                    await mensaje_sistema.edit(content=MENSAJE_ACTUALIZACION_SISTEMA)
                    await registrar_log(f"📤 Mensaje del sistema actualizado en #{CANAL_FALTAS}", categoria="faltas")
            else:
                mensaje_sistema = await canal_faltas.send(MENSAJE_ACTUALIZACION_SISTEMA)
                await registrar_log(f"📤 Mensaje del sistema creado en #{CANAL_FALTAS}", categoria="faltas")
            procesos_exitosos.append("Publicación/actualización de mensaje del sistema en #📤faltas")
            
            # Procesar usuarios en lotes
            for guild in bot.guilds:
                members = [member for member in guild.members if not member.bot]
                for i in range(0, len(members), 10):
                    batch = members[i:i+10]
                    for member in batch:
                        if member.id not in faltas_dict:
                            faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
                        await actualizar_mensaje_faltas(canal_faltas, member, faltas_dict[member.id]["faltas"], faltas_dict[member.id]["aciertos"], faltas_dict[member.id]["estado"])
                    await asyncio.sleep(2)
            procesos_exitosos.append("Actualización de estados de usuarios en #📤faltas")
        except discord.Forbidden:
            await registrar_log(f"❌ No tengo permisos para enviar/editar mensajes en #{CANAL_FALTAS}", categoria="faltas")
    
    canal_flujo = discord.utils.get(bot.get_all_channels(), name=CANAL_FLUJO_SOPORTE)
    if canal_flujo:
        try:
            async for msg in canal_flujo.history(limit=100):
                if msg.author == bot.user and msg.pinned:
                    lines = msg.content.split("\n")
                    question = None
                    response = []
                    for line in lines:
                        if line.startswith("**Pregunta:**"):
                            question = line.replace("**Pregunta:**", "").strip()
                        elif line.startswith("**Respuesta:**"):
                            response = [line.replace("**Respuesta:**", "").strip()]
                        elif question and not line.startswith("**"):
                            response.append(line.strip())
                    if question and response:
                        faq_data[question] = "\n".join(response)
            procesos_exitosos.append("Carga de FAQ desde #flujo-de-soporte")
        except discord.Forbidden:
            await registrar_log(f"❌ No tengo permisos para leer mensajes en #{CANAL_FLUJO_SOPORTE}", categoria="soporte")
    if not faq_data:
        faq_data.update(FAQ_FALLBACK)
        procesos_exitosos.append("Carga de FAQ por defecto")
    
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                if channel.name == CANAL_OBJETIVO:
                    await publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True)
                    procesos_exitosos.append(f"Publicación y fijado en #{CANAL_OBJETIVO}")
                elif channel.name == CANAL_REPORTES:
                    await publicar_mensaje_unico(channel, (
                        "🔖 **Cómo Reportar Correctamente**:\n\n"
                        "1. **Menciona a un usuario** (ej. @Sharon) para reportar una infracción.\n"
                        "2. **Selecciona la infracción** del menú que aparecerá. ✅\n"
                        "3. Usa `!permiso <días>` para solicitar un **permiso de inactividad** (máx. 7 días).\n\n"
                        "El bot registrará el reporte en #📝logs."
                    ), pinned=True)
                    procesos_exitosos.append(f"Publicación y fijado en #{CANAL_REPORTES}")
                elif channel.name == CANAL_SOPORTE:
                    await publicar_mensaje_unico(channel, (
                        "🔧 **Soporte Técnico**:\n\n"
                        "Escribe **'Hola'** para abrir el menú de opciones. ✅"
                    ), pinned=True)
                    procesos_exitosos.append(f"Publicación y fijado en #{CANAL_SOPORTE}")
                elif channel.name == CANAL_NORMAS_GENERALES:
                    await publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True)
                    procesos_exitosos.append(f"Publicación y fijado en #{CANAL_NORMAS_GENERALES}")
                elif channel.name == CANAL_ANUNCIOS:
                    await publicar_mensaje_unico(channel, MENSAJE_ANUNCIO_PERMISOS)
                    procesos_exitosos.append(f"Publicación en #{CANAL_ANUNCIOS}")
                await asyncio.sleep(1)
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para enviar/anclar mensajes en #{channel.name}", categoria="bot")
    
    # Evitar enviar el código completo en logs
    await registrar_log(f"💾 Código de main.py cargado correctamente", categoria="bot")
    procesos_exitosos.append("Carga de código sin errores")
    
    await registrar_log(
        f"✅ **Procesos iniciales completados**:\n" +
        "\n".join([f"- {proceso}" for proceso in procesos_exitosos]),
        categoria="bot"
    )
    
    await registrar_log(
        f"✅ **Bot actualizado y todos los procesos iniciales completados correctamente**. Nueva actualización ({datetime.datetime.utcnow().strftime('%Y-%m-%d')}) en ejecución.",
        categoria="actualizacion"
    )
    
    verificar_inactividad.start()
    clean_inactive_conversations.start()
    limpiar_mensajes_expulsados.start()
    resetear_faltas_diarias.start()

    await flush_log_queue()
    await registrar_log(f"✅ Bot al día tras completar el proceso: Inicialización", categoria="bot")

@bot.event
async def on_member_join(member):
    canal_presentate = discord.utils.get(member.guild.text_channels, name="👉preséntate")
    canal_faltas = discord.utils.get(member.guild.text_channels, name=CANAL_FALTAS)
    if canal_presentate:
        try:
            mensaje = (
                f"👋 **¡Bienvenid@ a VX {member.mention}!**\n\n"
                "**Sigue estos pasos**:\n"
                "📖 Lee las 3 guías\n"
                "✅ Revisa las normas\n"
                "🏆 Mira las victorias\n"
                "♟ Estudia las estrategias\n"
                "🏋 Luego solicita ayuda para tu primer post.\n\n"
                "📤 **Revisa tu estado** en #📤faltas para mantenerte al día.\n"
                "🚫 **Mensajes repetidos** serán eliminados en todos los canales (excepto #📝logs).\n"
                "⏳ Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para pausar la obligación de publicar (máx. 7 días)."
            )
            await canal_presentate.send(mensaje)
            await asyncio.sleep(1)
        except discord.Forbidden:
            await registrar_log(f"❌ No tengo permisos para enviar mensajes en #👉preséntate", categoria="miembros")
    if canal_faltas:
        try:
            if member.id not in faltas_dict:
                faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
            await actualizar_mensaje_faltas(canal_faltas, member, 0, 0, "OK")
        except discord.Forbidden:
            await registrar_log(f"❌ No tengo permisos para enviar/editar mensajes en #{CANAL_FALTAS} para {member.name}", categoria="faltas")
    await flush_log_queue()

@bot.command()
async def permiso(ctx, dias: int):
    if ctx.channel.name != CANAL_REPORTES:
        await ctx.send("⚠️ Usa este comando en #⛔reporte-de-incumplimiento.")
        return
    if dias > 7:
        await ctx.send(f"{ctx.author.mention} **El máximo permitido es 7 días**. Usa `!permiso <días>` con un valor entre 1 y 7.")
        await registrar_log(f"❌ Intento de permiso inválido por {ctx.author.name}: {dias} días", categoria="permisos")
        return
    if faltas_dict[ctx.author.id]["estado"] == "Baneado":
        await ctx.send(f"{ctx.author.mention} **No puedes solicitar un permiso mientras estás baneado**. Publica en #🧵go-viral para levantar el baneo.")
        await registrar_log(f"❌ Permiso denegado a {ctx.author.name}: usuario baneado", categoria="permisos")
        return
    ahora = datetime.datetime.utcnow()
    if permisos_inactividad[ctx.author.id] and (ahora - permisos_inactividad[ctx.author.id]["inicio"]).days < permisos_inactividad[ctx.author.id]["duracion"]:
        await ctx.send(f"{ctx.author.mention} **Ya tienes un permiso activo** hasta {permisos_inactividad[ctx.author.id]['inicio'] + datetime.timedelta(days=permisos_inactividad[ctx.author.id]['duracion'])}. Extiende antes de que expire.")
        await registrar_log(f"❌ Permiso denegado a {ctx.author.name}: permiso activo existente", categoria="permisos")
        return
    permisos_inactividad[ctx.author.id] = {"inicio": ahora, "duracion": dias}
    await ctx.send(f"✅ **Permiso de inactividad otorgado** a {ctx.author.mention} por {dias} días. No recibirás faltas por inactividad hasta {ahora + datetime.timedelta(days=dias)}. Extiende antes de que expire si necesitas más tiempo.")
    await registrar_log(f"✅ Permiso de inactividad otorgado a {ctx.author.name} por {dias} días", categoria="permisos")
    save_state()
    await flush_log_queue()

@tasks.loop(hours=24)
async def verificar_inactividad():
    canal = discord.utils.get(bot.get_all_channels(), name=CANAL_OBJETIVO)
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    ahora = datetime.datetime.utcnow()
    for user_id, ultima in list(ultima_publicacion_dict.items()):
        miembro = canal.guild.get_member(int(user_id))
        if not miembro or miembro.bot:
            continue
        permiso = permisos_inactividad[user_id]
        if permiso and (ahora - permiso["inicio"]).days < permiso["duracion"]:
            continue
        dias_inactivo = (ahora - ultima).days
        faltas = len([t for t in amonestaciones[user_id] if (ahora - t).total_seconds() < 7 * 86400])
        estado = faltas_dict[user_id]["estado"]
        aciertos = faltas_dict[user_id]["aciertos"]

        if dias_inactivo >= 3 and estado != "Baneado":
            amonestaciones[user_id].append(ahora)
            faltas = len([t for t in amonestaciones[user_id] if (ahora - t).total_seconds() < 7 * 86400])
            faltas_dict[user_id]["estado"] = "OK" if faltas < 3 else "Baneado"
            try:
                await miembro.send(
                    f"⚠️ **Falta por inactividad**: No has publicado en #🧵go-viral por {dias_inactivo} días.\n"
                    f"📊 Tienes {faltas} falta(s) por inactividad. Tres faltas resultan en un baneo de 7 días.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}.\n"
                    f"⏳ Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para pausar la obligación de publicar."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {miembro.name}", categoria="faltas")
            await registrar_log(f"⚠️ {miembro.name} recibió una falta por inactividad (Faltas: {faltas})", categoria="faltas")
            if faltas >= 3:
                role = discord.utils.get(canal.guild.roles, name="baneado")
                if role:
                    try:
                        await miembro.add_roles(role, reason="Inactividad > 3 días")
                        baneos_temporales[user_id] = ahora
                        faltas_dict[user_id]["estado"] = "Baneado"
                        await miembro.send(
                            f"🚫 **Baneado por 7 días**: Has acumulado 3 faltas por inactividad.\n"
                            f"📤 Revisa tu estado en #{CANAL_FALTAS}. Debes publicar dentro de los próximos 3 días para evitar expulsión."
                        )
                        await registrar_log(f"🚫 {miembro.name} baneado por 7 días por inactividad", categoria="faltas")
                        await asyncio.sleep(1)
                    except discord.Forbidden:
                        await registrar_log(f"❌ No tengo permisos para asignar el rol baneado a {miembro.name}", categoria="faltas")
                if canal_faltas:
                    await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "Baneado")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "OK" if faltas < 3 else "Baneado")
        elif dias_inactivo >= 3 and estado == "Baneado" and (ahora - baneos_temporales[user_id]).days >= 3:
            faltas_dict[user_id]["estado"] = "Expulsado"
            try:
                await miembro.send(
                    f"⛔ **Expulsado permanentemente**: No publicaste en #🧵go-viral por 3 días tras un baneo.\n"
                    f"📤 Tu estado final está en #{CANAL_FALTAS}."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar expulsión a {miembro.name}", categoria="faltas")
            try:
                await canal.guild.kick(miembro, reason="Expulsado por reincidencia en inactividad")
                await registrar_log(f"☠️ {miembro.name} expulsado por reincidencia", categoria="faltas")
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para expulsar a {miembro.name}", categoria="faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "Expulsado")
        elif dias_inactivo < 3 and estado == "OK":
            amonestaciones[user_id] = []
            try:
                await miembro.send(
                    f"✅ **Contador de inactividad reiniciado**: Has publicado en #🧵go-viral, tus faltas por inactividad se reiniciaron a 0.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar reinicio a {miembro.name}", categoria="faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "OK")
        save_state()
        await asyncio.sleep(0.5)
    await flush_log_queue()
    await registrar_log(f"✅ Bot al día tras completar el proceso: Verificación de inactividad", categoria="bot")
    await flush_log_queue()

@tasks.loop(hours=24)
async def resetear_faltas_diarias():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    ahora = datetime.datetime.utcnow()
    for user_id, data in list(faltas_dict.items()):
        if data["ultima_falta_time"] and (ahora - data["ultima_falta_time"]).total_seconds() >= 86400:
            miembro = discord.utils.get(bot.get_all_members(), id=int(user_id))
            if miembro:
                faltas_dict[user_id]["faltas"] = 0
                faltas_dict[user_id]["ultima_falta_time"] = None
                await actualizar_mensaje_faltas(canal_faltas, miembro, 0, data["aciertos"], data["estado"])
                await registrar_log(f"🔄 Faltas de {miembro.name} en #🧵go-viral reiniciadas a 0 tras 24 horas", categoria="faltas")
                try:
                    await miembro.send(
                        f"✅ **Faltas reiniciadas**: Tus faltas en #🧵go-viral se han reiniciado a 0 tras 24 horas.\n"
                        f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                    )
                    await asyncio.sleep(1)
                except:
                    await registrar_log(f"❌ No se pudo notificar reinicio de faltas a {miembro.name}", categoria="faltas")
        await asyncio.sleep(0.5)
    save_state()
    await flush_log_queue()
    await registrar_log(f"✅ Bot al día tras completar el proceso: Reseteo de faltas diarias", categoria="bot")
    await flush_log_queue()

@tasks.loop(minutes=1)
async def clean_inactive_conversations():
    canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
    if not canal_soporte:
        return
    ahora = datetime.datetime.utcnow()
    for user_id, data in list(active_conversations.items()):
        last_message_time = data.get("last_time")
        message_ids = data.get("message_ids", [])
        if last_message_time and (ahora - last_message_time).total_seconds() > INACTIVITY_TIMEOUT:
            for msg_id in message_ids:
                try:
                    msg = await canal_soporte.fetch_message(msg_id)
                    await msg.delete()
                    await registrar_log(f"🧹 Conversación limpiada para usuario {user_id} - Mensaje {msg_id} eliminado por inactividad", categoria="soporte")
                    await asyncio.sleep(0.5)
                except:
                    pass
            del active_conversations[user_id]
    save_state()
    await flush_log_queue()
    await registrar_log(f"✅ Bot al día tras completar el proceso: Limpieza de conversaciones inactivas", categoria="bot")
    await flush_log_queue()

@tasks.loop(hours=24)
async def limpiar_mensajes_expulsados():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if not canal_faltas:
        return
    ahora = datetime.datetime.utcnow()
    for user_id, data in list(faltas_dict.items()):
        if data["estado"] == "Expulsado" and (ahora - baneos_temporales[user_id]).days >= 7:
            mensaje_id = data["mensaje_id"]
            if mensaje_id:
                try:
                    mensaje = await canal_faltas.fetch_message(mensaje_id)
                    await mensaje.delete()
                    await registrar_log(f"🧹 Mensaje de usuario expulsado {user_id} eliminado de #{CANAL_FALTAS}", categoria="faltas")
                    await asyncio.sleep(0.5)
                except:
                    pass
                del faltas_dict[user_id]
    save_state()
    await flush_log_queue()
    await registrar_log(f"✅ Bot al día tras completar el proceso: Limpieza de mensajes de usuarios expulsados", categoria="bot")
    await flush_log_queue()

class ReportMenu(View):
    def __init__(self, reportado, autor):
        super().__init__(timeout=60)
        self.reportado = reportado
        self.autor = autor
        self.select = Select(
            placeholder="✉️ Selecciona la infracción",
            options=[
                SelectOption(label="RT", description="No hizo retweet"),
                SelectOption(label="LIKE", description="No dio like"),
                SelectOption(label="COMENTARIO", description="No comentó"),
                SelectOption(label="FORMATO", description="Formato incorrecto"),
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        razon = self.select.values[0].upper()
        ahora = datetime.datetime.utcnow()
        if self.reportado.id not in amonestaciones:
            amonestaciones[self.reportado.id] = []
        amonestaciones[self.reportado.id] = [
            t for t in amonestaciones[self.reportado.id] if (ahora - t).total_seconds() < 7 * 86400
        ]
        amonestaciones[self.reportado.id].append(ahora)
        cantidad = len(amonestaciones[self.reportado.id])
        canal_faltas = discord.utils.get(self.autor.guild.text_channels, name=CANAL_FALTAS)
        try:
            await self.reportado.send(
                f"⚠️ **Has recibido una amonestación por: {razon}**.\n"
                f"📌 Tres amonestaciones por inactividad en una semana te banean por 7 días.\n"
                f"🔀 Si reincides tras un baneo, serás expulsado definitivamente."
            )
            await asyncio.sleep(1)
        except:
            await registrar_log(f"❌ No se pudo notificar amonestación a {self.reportado.name}", categoria="reportes")
        logs_channel = discord.utils.get(self.autor.guild.text_channels, name=CANAL_LOGS)
        if logs_channel:
            await logs_channel.send(
                f"📜 **Reporte registrado**\n"
                f"👤 **Reportado**: {self.reportado.mention}\n"
                f"📣 **Reportado por**: {self.autor.mention}\n"
                f"📌 **Infracción**: `{razon}`\n"
                f"📆 **Amonestaciones en 7 días**: `{cantidad}`"
            )
            await asyncio.sleep(1)
        role_baneado = discord.utils.get(self.autor.guild.roles, name="baneado")
        if cantidad >= 6 and baneos_temporales[self.reportado.id]:
            try:
                await self.reportado.send("⛔ **Has sido expulsado permanentemente** del servidor por reincidir.")
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar expulsión a {self.reportado.name}", categoria="reportes")
            try:
                await self.autor.guild.kick(self.reportado, reason="Expulsado por reincidencia")
                await registrar_log(f"❌ {self.reportado.name} fue **expulsado permanentemente** por reincidir.", categoria="reportes")
                if canal_faltas:
                    faltas_dict[self.reportado.id]["estado"] = "Expulsado"
                    await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "Expulsado")
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para expulsar a {self.reportado.name}", categoria="reportes")
        elif cantidad >= 3 and not baneos_temporales[self.reportado.id]:
            if role_baneado:
                try:
                    await self.reportado.send("🚫 **Has sido baneado por 7 días** tras recibir 3 amonestaciones por inactividad.")
                    await self.reportado.add_roles(role_baneado, reason="3 amonestaciones en 7 días")
                    baneos_temporales[self.reportado.id] = ahora
                    await registrar_log(f"🚫 {self.reportado.name} ha sido **baneado por 7 días**.", categoria="reportes")
                    if canal_faltas:
                        faltas_dict[self.reportado.id]["estado"] = "Baneado"
                        await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "Baneado")
                    await asyncio.sleep(1)
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para asignar el rol baneado a {self.reportado.name}", categoria="reportes")
        elif cantidad < 3:
            await registrar_log(f"ℹ️ {self.reportado.name} ha recibido una amonestación, total: {cantidad}.", categoria="reportes")
        await interaction.response.send_message("✅ **Reporte registrado con éxito**.", ephemeral=True)
        await flush_log_queue()

class SupportMenu(View):
    def __init__(self, autor, query):
        super().__init__(timeout=60)
        self.autor = autor
        self.query = query
        self.select = Select(
            placeholder="🔧 Selecciona una opción",
            options=[
                SelectOption(label="Generar ticket", description="Crear un ticket para seguimiento"),
                SelectOption(label="Hablar con humano", description="Conectar con un administrador"),
                SelectOption(label="Cerrar consulta", description="Finalizar la interacción"),
                SelectOption(label="✅ ¿Cómo funciona VX?", description="Aprende cómo funciona la comunidad"),
                SelectOption(label="✅ ¿Cómo publico mi post?", description="Pasos para publicar tu contenido"),
                SelectOption(label="✅ ¿Cómo subo de nivel?", description="Cómo avanzar en la comunidad")
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        global ticket_counter, active_conversations
        user_id = self.autor.id
        await registrar_log(f"🔧 Soporte solicitado por {self.autor.name} (ID: {user_id}) - Consulta: {self.query} - Selección: {self.select.values[0]}", categoria="soporte")
        if self.select.values[0] == "Generar ticket":
            ticket_counter += 1
            ticket_id = f"ticket-{ticket_counter:03d}"
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await registrar_log(f"❌ Error: Admin user with ID {ADMIN_ID} not found", categoria="soporte")
                await interaction.response.send_message("❌ **No pude encontrar al administrador** para el ticket.", ephemeral=True)
                return
            try:
                await self.autor.send(f"🎫 **Se ha generado el ticket #{ticket_id}** para tu consulta: '{self.query}'. Un administrador te contactará pronto.")
                await admin.send(f"🎫 **Nuevo ticket #{ticket_id}** solicitado por {self.autor.mention} en #{CANAL_SOPORTE}: '{self.query}'. Por favor, responde.")
                await interaction.response.send_message(f"✅ **Ticket #{ticket_id} generado**. Te contactarán pronto.", ephemeral=True)
                await registrar_log(f"🎫 Ticket #{ticket_id} creado para {self.autor.name}", categoria="soporte")
                await asyncio.sleep(1)
            except Exception as e:
                await registrar_log(f"❌ Error generando ticket: {str(e)}", categoria="soporte")
                await interaction.response.send_message(f"❌ **Error al generar el ticket**: {str(e)}. Intenta de nuevo.", ephemeral=True)
        elif self.select.values[0] == "Hablar con humano":
            admin = bot.get_user(int(ADMIN_ID))
            await registrar_log(f"📞 Intentando notificar al admin con ID: {ADMIN_ID}", categoria="soporte")
            if not admin:
                await registrar_log(f"❌ Error: Admin user with ID {ADMIN_ID} not found", categoria="soporte")
                await interaction.response.send_message("❌ **No pude encontrar al administrador**. Intenta de nuevo más tarde.", ephemeral=True)
                return
            try:
                await self.autor.send(f"🔧 **Te he conectado con un administrador**. Por favor, espera a que {admin.mention} te responda.")
                await admin.send(f"⚠️ **Nuevo soporte solicitado** por {self.autor.mention} en #{CANAL_SOPORTE}: '{self.query}'. Por favor, contáctalo.")
                await interaction.response.send_message("✅ **He notificado a un administrador**. Te contactarán pronto.", ephemeral=True)
                await registrar_log(f"📞 Soporte transferido exitosamente a {admin.name}", categoria="soporte")
                await asyncio.sleep(1)
            except Exception as e:
                await registrar_log(f"❌ Error en transferencia de soporte: {str(e)}", categoria="soporte")
                await interaction.response.send_message(f"❌ **Error al contactar al administrador**: {str(e)}. Intenta de nuevo.", ephemeral=True)
        elif self.select.values[0] == "Cerrar consulta":
            canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
            if user_id in active_conversations and "message_ids" in active_conversations[user_id]:
                for msg_id in active_conversations[user_id]["message_ids"]:
                    try:
                        msg = await canal_soporte.fetch_message(msg_id)
                        await msg.delete()
                        await registrar_log(f"🧹 Conversación cerrada para usuario {user_id} - Mensaje {msg_id} eliminado", categoria="soporte")
                        await asyncio.sleep(0.5)
                    except:
                        pass
            del active_conversations[user_id]
            await interaction.response.send_message("✅ **Consulta cerrada**! Si necesitas más ayuda, vuelve cuando quieras. ¡Éxito con tu post y gracias por ser parte de VX! 🚀", ephemeral=True)
        elif self.select.values[0] in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
            response = faq_data.get(self.select.values[0], FAQ_FALLBACK.get(self.select.values[0], "No se encontró la respuesta."))
            await interaction.response.send_message(response, ephemeral=True)
            if user_id in active_conversations:
                active_conversations[user_id]["message_ids"].append(interaction.message.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
        await flush_log_queue()

@bot.event
async def on_message(message):
    global active_conversations, mensajes_recientes
    admin = bot.get_user(int(ADMIN_ID))
    if message.channel.name not in [CANAL_LOGS, CANAL_FALTAS]:
        canal_id = str(message.channel.id)
        mensaje_normalizado = message.content.strip().lower()
        if mensaje_normalizado:
            if any(mensaje_normalizado == msg.strip().lower() for msg in mensajes_recientes[canal_id]):
                try:
                    await message.delete()
                    await registrar_log(f"🗑️ Mensaje repetido eliminado en #{message.channel.name} por {message.author.name}: {message.content[:50]}...", categoria="repetidos")
                    if message.author == bot.user and admin:
                        try:
                            await admin.send(
                                f"⚠️ **Mensaje del bot eliminado**: Un mensaje repetido del bot en #{message.channel.name} fue eliminado: {message.content[:50]}..."
                            )
                            await asyncio.sleep(1)
                        except:
                            await registrar_log(f"❌ No se pudo notificar eliminación de mensaje del bot al admin", categoria="repetidos")
                    elif message.author != bot.user:
                        try:
                            await message.author.send(
                                f"⚠️ **Mensaje repetido eliminado**: No repitas mensajes en #{message.channel.name}. "
                                f"Por favor, envía contenido nuevo para mantener el servidor limpio."
                            )
                            await asyncio.sleep(1)
                        except:
                            await registrar_log(f"❌ No se pudo notificar mensaje repetido a {message.author.name}", categoria="repetidos")
                    await flush_log_queue()
                    return
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para eliminar mensajes en #{message.channel.name}", categoria="repetidos")
            mensajes_recientes[canal_id].append(message.content)
            if len(mensajes_recientes[canal_id]) > MAX_MENSAJES_RECIENTES:
                mensajes_recientes[canal_id].pop(0)
            save_state()
    
    await registrar_log(f"💬 Mensaje en #{message.channel.name} por {message.author.name} (ID: {message.author.id}): {message.content}", categoria="mensajes")
    
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        if message.mentions:
            reportado = message.mentions[0]
            await message.channel.send(
                f"📃 **Reportando a {reportado.mention}**\nSelecciona la infracción que ha cometido:",
                view=ReportMenu(reportado, message.author)
            )
            await message.delete()
            await asyncio.sleep(1)
        else:
            await message.channel.send("⚠️ **Por favor, menciona a un usuario** para reportar (ej. @Sharon) o usa `!permiso <días>` para solicitar inactividad.")
            await asyncio.sleep(1)
    elif message.channel.name == CANAL_SOPORTE and not message.author.bot:
        user_id = message.author.id
        if user_id not in active_conversations:
            active_conversations[user_id] = {"message_ids": [], "last_time": datetime.datetime.utcnow()}
        if message.content.lower() in ["salir", "cancelar", "fin", "ver reglas"]:
            if message.content.lower() == "ver reglas":
                msg = await message.channel.send(MENSAJE_NORMAS)
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
                faltas_dict[user_id]["aciertos"] += 1
                if canal_faltas:
                    await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[user_id]["faltas"], faltas_dict[user_id]["aciertos"], faltas_dict[user_id]["estado"])
            else:
                msg = await message.channel.send("✅ **Consulta cerrada**. ¡Vuelve si necesitas ayuda!")
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
            await message.delete()
            await asyncio.sleep(1)
            await flush_log_queue()
            return
        msg = await message.channel.send("👋 **Usa el menú 'Selecciona una opción'** para obtener ayuda.", view=SupportMenu(message.author, message.content))
        active_conversations[user_id]["message_ids"].append(msg.id)
        active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
        await message.delete()
        await asyncio.sleep(1)
    elif message.channel.name == CANAL_OBJETIVO and not message.author.bot:
        ahora = datetime.datetime.utcnow()
        urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
        if len(urls) != 1 or (len(urls) == 1 and message.content.strip() != urls[0]):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **Solo se permite un link válido de X sin texto adicional**. Formato: `https://x.com/usuario/status/1234567890123456789`. Tu calificación se ha reducido en 1%."
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Mensaje eliminado en #{CANAL_OBJETIVO} por {message.author.name} por formato inválido", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por formato incorrecto**: Tu publicación no cumple con el formato.\n"
                    f"📊 **Faltas en #🧵go-viral**: {faltas_dict[message.author.id]['faltas']}. Tu calificación se ha reducido en 1%.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}. Las faltas se reinician cada 24 horas."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            await flush_log_queue()
            return
        url = urls[0].split('?')[0]
        url_pattern = r"https://x\.com/[^/]+/status/\d+"
        if not re.match(url_pattern, url):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **El enlace no tiene el formato correcto**. Formato: `https://x.com/usuario/status/1234567890123456789`. Tu calificación se ha reducido en 1%."
﻿
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Mensaje eliminado en #{CANAL_OBJETIVO} por {message.author.name} por URL inválida", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por URL inválida**: Tu enlace no tiene el formato correcto.\n"
                    f"📊 **Faltas en #🧵go-viral**: {faltas_dict[message.author.id]['faltas']}. Tu calificación se ha reducido en 1%.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}. Las faltas se reinician cada 24 horas."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            await flush_log_queue()
            return
        if '?' in urls[0]:
            await registrar_log(f"🔧 URL limpiada de {urls[0]} a {url} para usuario {message.author.name}", categoria="publicaciones")
        new_message = message
        mensajes = []
        async for msg in message.channel.history(limit=100):
            if msg.id == new_message.id or msg.author == bot.user:
                continue
            mensajes.append(msg)
        ultima_publicacion = None
        for msg in mensajes:
            if msg.author == message.author:
                ultima_publicacion = msg
                break
        if not ultima_publicacion:
            ultima_publicacion_dict[message.author.id] = ahora
            faltas_dict[message.author.id]["aciertos"] += 1
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            await registrar_log(f"📅 Nueva publicación inicial de {message.author.name} en #{CANAL_OBJETIVO}", categoria="publicaciones")
            await flush_log_queue()
            return
        diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
        publicaciones_despues = [m for m in mensajes if m.created_at > ultima_publicacion.created_at and m.author != message.author]
        no_apoyados = []
        for msg in mensajes:
            if msg.created_at > ultima_publicacion.created_at and msg.author != message.author:
                apoyo = False
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "🔥":
                        async for user in reaction.users():
                            if user == message.author:
                                apoyo = True
                                faltas_dict[user.id]["aciertos"] += 1
                                if canal_faltas:
                                    await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], faltas_dict[user.id]["estado"])
                                break
                if not apoyo:
                    no_apoyados.append(msg)
        if no_apoyados:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **Debes reaccionar con 🔥 a todas las publicaciones desde tu última publicación** antes de publicar. Tu calificación se ha reducido en 1%."
            )
            await advertencia.delete(delay=15)
            urls_faltantes = [m.jump_url for m in no_apoyados]
            try:
                await message.author.send(
                    f"⚠️ **Falta por no reaccionar con 🔥**: Te faltan reacciones a los siguientes posts:\n" +
                    "\n".join(urls_faltantes) +
                    f"\n📊 **Faltas en #🧵go-viral**: {faltas_dict[message.author.id]['faltas']}. Tu calificación se ha reducido en 1%.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}. Las faltas se reinician cada 24 horas."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            await registrar_log(f"❌ Publicación denegada a {message.author.name} por falta de reacciones 🔥 a {len(no_apoyados)} posts", categoria="publicaciones")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            await flush_log_queue()
            return
        if len(publicaciones_despues) < 1 and diferencia.total_seconds() < 86400:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **Aún no puedes publicar**. Debes esperar al menos 24 horas desde tu última publicación si no hay otras publicaciones. Tu calificación se ha reducido en 1%."
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"⏳ Publicación denegada a {message.author.name} por tiempo insuficiente (<24h)", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por tiempo insuficiente**: No has esperado 24 horas desde tu última publicación.\n"
                    f"📊 **Faltas en #🧵go-viral**: {faltas_dict[message.author.id]['faltas']}. Tu calificación se ha reducido en 1%.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}. Las faltas se reinician cada 24 horas."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            await flush_log_queue()
            return
        def check_reaccion_propia(reaction, user):
            return reaction.message.id == new_message.id and str(reaction.emoji) == "👍" and user == message.author
        try:
            await bot.wait_for("reaction_add", timeout=60, check=check_reaccion_propia)
            faltas_dict[message.author.id]["aciertos"] += 1
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
        except:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **Tu publicación fue eliminada**. Debes reaccionar con 👍 a tu propio mensaje para validarlo. Tu calificación se ha reducido en 1%."
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Publicación eliminada de {message.author.name} por falta de reacción 👍", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por no reaccionar con 👍**: No reaccionaste a tu propia publicación.\n"
                    f"📊 **Faltas en #🧵go-viral**: {faltas_dict[message.author.id]['faltas']}. Tu calificación se ha reducido en 1%.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}. Las faltas se reinician cada 24 horas."
                )
                await asyncio.sleep(1)
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            await flush_log_queue()
            return
        ultima_publicacion_dict[message.author.id] = ahora
        await registrar_log(f"✅ Publicación validada de {message.author.name} en #{CANAL_OBJETIVO}", categoria="publicaciones")
        await flush_log_queue()
    elif message.channel.name in [CANAL_NORMAS_GENERALES, CANAL_X_NORMAS] and not message.author.bot:
        canal_anuncios = discord
