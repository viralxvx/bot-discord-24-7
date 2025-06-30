from flask import Flask, jsonify
from threading import Thread
import discord
import re
import os
import datetime
import json
import asyncio
import threading
from discord.ext import commands, tasks
from collections import defaultdict
from discord.ui import View, Select
from discord import SelectOption, Interaction
import sys

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
MAX_MENSAJES_RECIENTES = 10  # Número máximo de mensajes recientes a rastrear por canal
MAX_LOG_LENGTH = 500  # Longitud máxima para mensajes de log
LOG_BATCH_DELAY = 1.0  # Delay entre batches de logs (segundos)

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    
    ultima_publicacion_dict = defaultdict(
        lambda: datetime.datetime.now(datetime.timezone.utc),
        {k: load_datetime(v) for k, v in state.get("ultima_publicacion_dict", {}).items()}
    )
    
    amonestaciones = defaultdict(
        list, 
        {k: [load_datetime(t) for t in v] for k, v in state.get("amonestaciones", {}).items()}
    )
    
    baneos_temporales = defaultdict(
        lambda: None,
        {k: load_datetime(v) for k, v in state.get("baneos_temporales", {}).items()}
    )
    
    permisos_inactividad = defaultdict(
        lambda: None,
        {k: {"inicio": load_datetime(v["inicio"]), "duracion": v["duracion"]} if v else None 
         for k, v in state.get("permisos_inactividad", {}).items()}
    )
    
    ticket_counter = state.get("ticket_counter", 0)
    active_conversations = state.get("active_conversations", {})
    faq_data = state.get("faq_data", {})
    
    faltas_dict = defaultdict(
        lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None},
        {
            k: {
                "faltas": v["faltas"],
                "aciertos": v["aciertos"],
                "estado": v["estado"],
                "mensaje_id": v["mensaje_id"],
                "ultima_falta_time": load_datetime(v["ultima_falta_time"]) if v["ultima_falta_time"] else None
            } for k, v in state.get("faltas_dict", {}).items()
        }
    )
    
    mensajes_recientes = defaultdict(list, state.get("mensajes_recientes", {}))
except FileNotFoundError:
    ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
    amonestaciones = defaultdict(list)
    baneos_temporales = defaultdict(lambda: None)
    permisos_inactividad = defaultdict(lambda: None)
    ticket_counter = 0
    active_conversations = {}
    faq_data = {}
    faltas_dict = defaultdict(lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None})
    mensajes_recientes = defaultdict(list)

def save_state():
    state = {
        "ultima_publicacion_dict": {str(k): v.isoformat() for k, v in ultima_publicacion_dict.items()},
        "amonestaciones": {str(k): [t.isoformat() for t in v] for k, v in amonestaciones.items()},
        "baneos_temporales": {str(k): v.isoformat() if v else None for k, v in baneos_temporales.items()},
        "permisos_inactividad": {str(k): {"inicio": v["inicio"].isoformat(), "duracion": v["duracion"]} if v else None for k, v in permisos_inactividad.items()},
        "ticket_counter": ticket_counter,
        "active_conversations": active_conversations,
        "faq_data": faq_data,
        "faltas_dict": {
            str(k): {
                "faltas": v["faltas"],
                "aciertos": v["aciertos"],
                "estado": v["estado"],
                "mensaje_id": v["mensaje_id"],
                "ultima_falta_time": v["ultima_falta_time"].isoformat() if v["ultima_falta_time"] else None
            } for k, v in faltas_dict.items()
        },
        "mensajes_recientes": {str(k): v for k, v in mensajes_recientes.items()}
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

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

def calcular_calificacion(faltas):
    porcentaje = max(0, 100 - faltas)
    barras = int(porcentaje // 10)
    barra_visual = "[" + "█" * barras + " " * (10 - barras) + "]"
    return porcentaje, f"{barra_visual} {porcentaje:.2f}%"

async def actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, estado):
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
            except discord.errors.NotFound:
                mensaje = await canal_faltas.send(contenido)
                faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
        else:
            mensaje = await canal_faltas.send(contenido)
            faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
        save_state()
    except Exception as e:
        pass

async def registrar_log(texto, categoria="general"):
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if canal_log and texto:
        try:
            # Acortar texto si es demasiado largo
            if len(texto) > MAX_LOG_LENGTH:
                texto = texto[:MAX_LOG_LENGTH] + "..."
                
            # Formato compacto de timestamp
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
            await canal_log.send(f"[{timestamp}] [{categoria.upper()}] {texto}")
        except:
            pass

async def batch_log(messages):
    """Envía logs en batches con delay para evitar rate limiting"""
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if not canal_log:
        return
        
    for batch in messages:
        if not batch:
            continue
            
        # Combinar múltiples mensajes en uno solo
        combined = "\n".join(batch)
        try:
            await canal_log.send(combined)
        except:
            pass
        
        # Esperar antes del próximo batch
        await asyncio.sleep(LOG_BATCH_DELAY)

async def verificar_historial_repetidos():
    pass  # Eliminado para optimizar inicio

async def publicar_mensaje_unico(canal, contenido, pinned=False):
    try:
        contenido_normalizado = contenido.strip().lower()
        mensajes_vistos = set()
        mensajes_a_eliminar = []
        async for msg in canal.history(limit=None):
            msg_normalizado = msg.content.strip().lower()
            if msg.author == bot.user:
                if msg_normalizado == contenido_normalizado or msg_normalizado in mensajes_vistos:
                    mensajes_a_eliminar.append(msg)
            if pinned and msg.pinned and msg.author == bot.user:
                mensajes_a_eliminar.append(msg)
        for msg in mensajes_a_eliminar:
            try:
                await msg.delete()
            except:
                pass
        mensaje = await canal.send(contenido)
        if pinned:
            await mensaje.pin()
        return mensaje
    except:
        return None

@bot.event
async def on_ready():
    global ticket_counter, faq_data
    print(f"Bot conectado como {bot.user}")
    
    # Lista para acumular logs y enviar en batches
    log_batches = []
    current_batch = []
    
    def add_log(texto, categoria="bot"):
        nonlocal current_batch
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{categoria.upper()}] {texto}"
        if len("\n".join(current_batch) + log_entry) > 1900:
            log_batches.append(current_batch)
            current_batch = []
        current_batch.append(log_entry)
    
    add_log(f"Bot iniciado")
    
    procesos_exitosos = []
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if canal_faltas:
        try:
            mensaje_sistema = None
            async for msg in canal_faltas.history(limit=100):
                if msg.author == bot.user and msg.content.startswith("🚫 **FALTAS DE LOS USUARIOS**"):
                    mensaje_sistema = msg
                    break
            if mensaje_sistema:
                if mensaje_sistema.content != MENSAJE_ACTUALIZACION_SISTEMA:
                    await mensaje_sistema.edit(content=MENSAJE_ACTUALIZACION_SISTEMA)
            else:
                mensaje_sistema = await canal_faltas.send(MENSAJE_ACTUALIZACION_SISTEMA)
            procesos_exitosos.append("Mensaje sistema faltas")
            
            for guild in bot.guilds:
                for member in guild.members:
                    if member.bot:
                        continue
                    if member.id not in faltas_dict:
                        faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
                    await actualizar_mensaje_faltas(canal_faltas, member, faltas_dict[member.id]["faltas"], faltas_dict[member.id]["aciertos"], faltas_dict[member.id]["estado"])
            procesos_exitosos.append(f"Actualizados {len(guild.members)} miembros")
        except:
            add_log("Error en canal faltas", "error")
    
    canal_flujo = discord.utils.get(bot.get_all_channels(), name=CANAL_FLUJO_SOPORTE)
    if canal_flujo:
        try:
            async for msg in canal_flujo.history(limit=100):
                if msg.author == bot.user and msg.pinned:
                    lines = msg.content.split("\n")
                    question = None
                    response = []
                    for line in lines:
                        if line.startswith("**Pregunta:"):
                            question = line.replace("**Pregunta:**", "").strip()
                        elif line.startswith("**Respuesta:**"):
                            response = [line.replace("**Respuesta:**", "").strip()]
                        elif question and not line.startswith("**"):
                            response.append(line.strip())
                    if question and response:
                        faq_data[question] = "\n".join(response)
            procesos_exitosos.append("Carga FAQ")
        except:
            pass
    if not faq_data:
        faq_data.update(FAQ_FALLBACK)
        procesos_exitosos.append("FAQ por defecto")
    
    tasks = []
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                if channel.name == CANAL_OBJETIVO:
                    tasks.append(publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True))
                    procesos_exitosos.append(f"Publicado #{CANAL_OBJETIVO}")
                elif channel.name == CANAL_REPORTES:
                    content = (
                        "🔖 **Cómo Reportar Correctamente**:\n\n"
                        "1. **Menciona a un usuario** (ej. @Sharon) para reportar una infracción.\n"
                        "2. **Selecciona la infracción** del menú que aparecerá. ✅\n"
                        "3. Usa `!permiso <días>` para solicitar un **permiso de inactividad** (máx. 7 días).\n\n"
                        "El bot registrará el reporte en #📝logs."
                    )
                    tasks.append(publicar_mensaje_unico(channel, content, pinned=True))
                    procesos_exitosos.append(f"Publicado #{CANAL_REPORTES}")
                elif channel.name == CANAL_SOPORTE:
                    content = (
                        "🔧 **Soporte Técnico**:\n\n"
                        "Escribe **'Hola'** para abrir el menú de opciones. ✅"
                    )
                    tasks.append(publicar_mensaje_unico(channel, content, pinned=True))
                    procesos_exitosos.append(f"Publicado #{CANAL_SOPORTE}")
                elif channel.name == CANAL_NORMAS_GENERALES:
                    tasks.append(publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True))
                    procesos_exitosos.append(f"Publicado #{CANAL_NORMAS_GENERALES}")
                elif channel.name == CANAL_ANUNCIOS:
                    tasks.append(publicar_mensaje_unico(channel, MENSAJE_ANUNCIO_PERMISOS))
                    procesos_exitosos.append(f"Publicado #{CANAL_ANUNCIOS}")
            except:
                pass
    
    # Ejecutar tareas de publicación en paralelo
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Agregar logs de procesos exitosos
    if procesos_exitosos:
        add_log("Procesos completados: " + ", ".join(procesos_exitosos))
    
    # Enviar todos los logs acumulados en batches
    if current_batch:
        log_batches.append(current_batch)
    
    if log_batches:
        await batch_log(log_batches)
    
    # Iniciar tareas programadas
    verificar_inactividad.start()
    clean_inactive_conversations.start()
    limpiar_mensajes_expulsados.start()
    resetear_faltas_diarias.start()

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
        except discord.Forbidden:
            pass
    if canal_faltas:
        try:
            if member.id not in faltas_dict:
                faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
            await actualizar_mensaje_faltas(canal_faltas, member, 0, 0, "OK")
        except discord.Forbidden:
            pass
    await registrar_log(f"👤 Nuevo miembro: {member.name}", categoria="miembros")

@bot.command()
async def permiso(ctx, dias: int):
    if ctx.channel.name != CANAL_REPORTES:
        await ctx.send("⚠️ Usa este comando en #⛔reporte-de-incumplimiento.")
        return
    if dias > 7:
        await ctx.send(f"{ctx.author.mention} **Máximo 7 días**")
        return
    if faltas_dict[ctx.author.id]["estado"] == "Baneado":
        await ctx.send(f"{ctx.author.mention} **No puedes solicitar permiso baneado**")
        return
    ahora = datetime.datetime.now(datetime.timezone.utc)
    if permisos_inactividad[ctx.author.id] and (ahora - permisos_inactividad[ctx.author.id]["inicio"]).days < permisos_inactividad[ctx.author.id]["duracion"]:
        await ctx.send(f"{ctx.author.mention} **Ya tienes permiso activo**")
        return
    permisos_inactividad[ctx.author.id] = {"inicio": ahora, "duracion": dias}
    await ctx.send(f"✅ **Permiso otorgado** a {ctx.author.mention} por {dias} días")
    await registrar_log(f"Permiso: {ctx.author.name} por {dias}d", categoria="permisos")
    save_state()

@tasks.loop(hours=24)
async def verificar_inactividad():
    canal = discord.utils.get(bot.get_all_channels(), name=CANAL_OBJETIVO)
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, ultima in list(ultima_publicacion_dict.items()):
        miembro = canal.guild.get_member(int(user_id))
        if not miembro or miembro.bot:
            continue
        permiso = permisos_inactividad[user_id]
        if permiso and (ahora - permiso["inicio"]).days < permiso["duracion"]:
            continue
        dias_inactivo = (ahora - ultima).days
        faltas = amonestaciones[user_id]
        estado = faltas_dict[user_id]["estado"]
        aciertos = faltas_dict[user_id]["aciertos"]

        if dias_inactivo >= 3 and estado != "Baneado":
            amonestaciones[user_id].append(ahora)
            faltas = len([t for t in amonestaciones[user_id] if (ahora - t).total_seconds() < 7 * 86400])
            faltas_dict[user_id]["estado"] = "OK" if faltas < 3 else "Baneado"
            try:
                await miembro.send(
                    f"⚠️ **Falta por inactividad**: Llevas {dias_inactivo} días sin publicar\n"
                    f"📊 Faltas: {faltas}/3\n"
                    f"⏳ Usa `!permiso <días>` para pausar"
                )
            except:
                pass
            if faltas >= 3:
                role = discord.utils.get(canal.guild.roles, name="baneado")
                if role:
                    try:
                        await miembro.add_roles(role, reason="Inactividad > 3 días")
                        baneos_temporales[user_id] = ahora
                        faltas_dict[user_id]["estado"] = "Baneado"
                        await miembro.send(
                            f"🚫 **Baneado por 7 días**: 3 faltas por inactividad\n"
                            f"📤 Publica en #🧵go-viral para levantar baneo"
                        )
                        await registrar_log(f"🚫 {miembro.name} baneado", categoria="faltas")
                    except discord.Forbidden:
                        pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "OK" if faltas < 3 else "Baneado")
        elif dias_inactivo >= 3 and estado == "Baneado" and (ahora - baneos_temporales[user_id]).days >= 3:
            faltas_dict[user_id]["estado"] = "Expulsado"
            try:
                await miembro.send(
                    f"⛔ **Expulsado permanentemente** por inactividad"
                )
            except:
                pass
            try:
                await canal.guild.kick(miembro, reason="Expulsado por reincidencia en inactividad")
                await registrar_log(f"☠️ {miembro.name} expulsado", categoria="faltas")
            except discord.Forbidden:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "Expulsado")
        elif dias_inactivo < 3 and estado == "OK":
            amonestaciones[user_id] = []
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "OK")
        save_state()

@tasks.loop(hours=24)
async def resetear_faltas_diarias():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(faltas_dict.items()):
        if data["ultima_falta_time"] and (ahora - data["ultima_falta_time"]).total_seconds() >= 86400:
            miembro = discord.utils.get(bot.get_all_members(), id=int(user_id))
            if miembro:
                faltas_dict[user_id]["faltas"] = 0
                faltas_dict[user_id]["ultima_falta_time"] = None
                await actualizar_mensaje_faltas(canal_faltas, miembro, 0, data["aciertos"], data["estado"])
                try:
                    await miembro.send(
                        f"✅ **Faltas reiniciadas** en #🧵go-viral"
                    )
                except:
                    pass
    save_state()

@tasks.loop(minutes=1)
async def clean_inactive_conversations():
    canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
    if not canal_soporte:
        return
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(active_conversations.items()):
        last_message_time = data.get("last_time")
        message_ids = data.get("message_ids", [])
        if last_message_time and (ahora - last_message_time).total_seconds() > INACTIVITY_TIMEOUT:
            for msg_id in message_ids:
                try:
                    msg = await canal_soporte.fetch_message(msg_id)
                    await msg.delete()
                except:
                    pass
            del active_conversations[user_id]
    save_state()

@tasks.loop(hours=24)
async def limpiar_mensajes_expulsados():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if not canal_faltas:
        return
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(faltas_dict.items()):
        if data["estado"] == "Expulsado" and (ahora - baneos_temporales[user_id]).days >= 7:
            mensaje_id = data["mensaje_id"]
            if mensaje_id:
                try:
                    mensaje = await canal_faltas.fetch_message(mensaje_id)
                    await mensaje.delete()
                except:
                    pass
                del faltas_dict[user_id]
    save_state()

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
        ahora = datetime.datetime.now(datetime.timezone.utc)
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
                f"⚠️ **Amonestación por: {razon}**\n"
                f"📌 3 amonestaciones = baneo 7 días"
            )
        except:
            pass
        logs_channel = discord.utils.get(self.autor.guild.text_channels, name=CANAL_LOGS)
        if logs_channel:
            await logs_channel.send(
                f"📜 **Reporte**\n"
                f"👤 Reportado: {self.reportado.mention}\n"
                f"📣 Por: {self.autor.mention}\n"
                f"📌 Infracción: `{razon}`\n"
                f"📆 Amonestaciones: `{cantidad}`"
            )
        role_baneado = discord.utils.get(self.autor.guild.roles, name="baneado")
        if cantidad >= 6 and baneos_temporales[self.reportado.id]:
            try:
                await self.reportado.send("⛔ **Expulsado permanentemente**")
            except:
                pass
            try:
                await self.autor.guild.kick(self.reportado, reason="Expulsado por reincidencia")
                if canal_faltas:
                    faltas_dict[self.reportado.id]["estado"] = "Expulsado"
                    await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "Expulsado")
            except discord.Forbidden:
                pass
        elif cantidad >= 3 and not baneos_temporales[self.reportado.id]:
            if role_baneado:
                try:
                    await self.reportado.send("🚫 **Baneado por 7 días**")
                    await self.reportado.add_roles(role_baneado, reason="3 amonestaciones en 7 días")
                    baneos_temporales[self.reportado.id] = ahora
                    if canal_faltas:
                        faltas_dict[self.reportado.id]["estado"] = "Baneado"
                        await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "Baneado")
                except discord.Forbidden:
                    pass
        await interaction.response.send_message("✅ **Reporte registrado**", ephemeral=True)
        await registrar_log(f"Reporte: {self.autor.name} → {self.reportado.name} ({razon})", categoria="reportes")

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
        if self.select.values[0] == "Generar ticket":
            ticket_counter += 1
            ticket_id = f"ticket-{ticket_counter:03d}"
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await interaction.response.send_message("❌ **Error al generar ticket**", ephemeral=True)
                return
            try:
                await self.autor.send(f"🎫 **Ticket #{ticket_id} generado**")
                await admin.send(f"🎫 **Ticket #{ticket_id}** por {self.autor.mention}: '{self.query}'")
                await interaction.response.send_message(f"✅ **Ticket #{ticket_id} generado**", ephemeral=True)
                await registrar_log(f"Ticket #{ticket_id}: {self.autor.name}", categoria="soporte")
            except Exception:
                await interaction.response.send_message("❌ **Error al generar ticket**", ephemeral=True)
        elif self.select.values[0] == "Hablar con humano":
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await interaction.response.send_message("❌ **Error al contactar admin**", ephemeral=True)
                return
            try:
                await self.autor.send(f"🔧 **Conectado con administrador**")
                await admin.send(f"⚠️ **Soporte solicitado** por {self.autor.mention}: '{self.query}'")
                await interaction.response.send_message("✅ **Admin notificado**", ephemeral=True)
            except Exception:
                await interaction.response.send_message("❌ **Error al contactar admin**", ephemeral=True)
        elif self.select.values[0] == "Cerrar consulta":
            canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
            if user_id in active_conversations and "message_ids" in active_conversations[user_id]:
                for msg_id in active_conversations[user_id]["message_ids"]:
                    try:
                        msg = await canal_soporte.fetch_message(msg_id)
                        await msg.delete()
                    except:
                        pass
            del active_conversations[user_id]
            await interaction.response.send_message("✅ **Consulta cerrada**", ephemeral=True)
        elif self.select.values[0] in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
            response = faq_data.get(self.select.values[0], FAQ_FALLBACK.get(self.select.values[0], "No se encontró respuesta"))
            await interaction.response.send_message(response, ephemeral=True)
            if user_id in active_conversations:
                active_conversations[user_id]["message_ids"].append(interaction.message.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)

@bot.event
async def on_message(message):
    global active_conversations, mensajes_recientes
    if message.channel.name not in [CANAL_LOGS, CANAL_FALTAS]:
        canal_id = str(message.channel.id)
        mensaje_normalizado = message.content.strip().lower()
        if mensaje_normalizado:
            if any(mensaje_normalizado == msg.strip().lower() for msg in mensajes_recientes[canal_id]):
                try:
                    await message.delete()
                    if message.author != bot.user:
                        try:
                            await message.author.send(
                                f"⚠️ **Mensaje repetido eliminado** en #{message.channel.name}"
                            )
                        except:
                            pass
                except discord.Forbidden:
                    pass
            mensajes_recientes[canal_id].append(message.content)
            if len(mensajes_recientes[canal_id]) > MAX_MENSAJES_RECIENTES:
                mensajes_recientes[canal_id].pop(0)
            save_state()
    
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        if message.mentions:
            reportado = message.mentions[0]
            await message.channel.send(
                f"📃 **Reportando a {reportado.mention}**",
                view=ReportMenu(reportado, message.author)
            )
            await message.delete()
        else:
            await message.channel.send("⚠️ **Menciona un usuario** o usa `!permiso <días>`")
    elif message.channel.name == CANAL_SOPORTE and not message.author.bot:
        user_id = message.author.id
        if user_id not in active_conversations:
            active_conversations[user_id] = {"message_ids": [], "last_time": datetime.datetime.now(datetime.timezone.utc)}
        if message.content.lower() in ["salir", "cancelar", "fin", "ver reglas"]:
            if message.content.lower() == "ver reglas":
                msg = await message.channel.send(MENSAJE_NORMAS)
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
                faltas_dict[user_id]["aciertos"] += 1
                if canal_faltas:
                    await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[user_id]["faltas"], faltas_dict[user_id]["aciertos"], faltas_dict[user_id]["estado"])
            else:
                msg = await message.channel.send("✅ **Consulta cerrada**")
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
            await message.delete()
            return
        msg = await message.channel.send("👋 **Selecciona una opción**", view=SupportMenu(message.author, message.content))
        active_conversations[user_id]["message_ids"].append(msg.id)
        active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
        await message.delete()
    elif message.channel.name == CANAL_OBJETIVO and not message.author.bot:
        ahora = datetime.datetime.now(datetime.timezone.utc)
        urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
        if len(urls) != 1 or (len(urls) == 1 and message.content.strip() != urls[0]):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **Formato incorrecto**"
            )
            await advertencia.delete(delay=15)
            try:
                await message.author.send(
                    f"⚠️ **Falta**: Formato incorrecto en #🧵go-viral"
                )
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
        url = urls[0].split('?')[0]
        url_pattern = r"https://x\.com/[^/]+/status/\d+"
        if not re.match(url_pattern, url):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **URL inválida**"
            )
            await advertencia.delete(delay=15)
            try:
                await message.author.send(
                    f"⚠️ **Falta**: URL inválida en #🧵go-viral"
                )
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
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
                f"{message.author.mention} **Falta de reacciones**"
            )
            await advertencia.delete(delay=15)
            try:
                await message.author.send(
                    f"⚠️ **Falta**: Reacciones pendientes en #🧵go-viral"
                )
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
        if len(publicaciones_despues) < 1 and diferencia.total_seconds() < 86400:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["ultima_falta_time"] = ahora
            advertencia = await message.channel.send(
                f"{message.author.mention} **Espera 24h**"
            )
            await advertencia.delete(delay=15)
            try:
                await message.author.send(
                    f"⚠️ **Falta**: Publicación antes de 24h"
                )
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
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
                f"{message.author.mention} **Falta reacción propia**"
            )
            await advertencia.delete(delay=15)
            try:
                await message.author.send(
                    f"⚠️ **Falta**: Sin reacción 👍 propia"
                )
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], faltas_dict[message.author.id]["estado"])
            return
        ultima_publicacion_dict[message.author.id] = ahora
    elif message.channel.name in [CANAL_NORMAS_GENERALES, CANAL_X_NORMAS] and not message.author.bot:
        canal_anuncios = discord.utils.get(message.guild.text_channels, name=CANAL_ANUNCIOS)
        if canal_anuncios:
            await publicar_mensaje_unico(canal_anuncios, (
                f"📢 **Norma actualizada**: {message.channel.mention}"
            ))
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.message.channel.name != CANAL_OBJETIVO:
        return
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    autor = reaction.message.author
    emoji_valido = "👍" if user == autor else "🔥"
    ahora = datetime.datetime.now(datetime.timezone.utc)
    if reaction.message.channel.name == CANAL_OBJETIVO:
        if str(reaction.emoji) != emoji_valido:
            await reaction.remove(user)
            faltas_dict[user.id]["faltas"] += 1
            faltas_dict[user.id]["ultima_falta_time"] = ahora
            advertencia = await reaction.message.channel.send(
                f"{user.mention} **Emoji incorrecto**"
            )
            await advertencia.delete(delay=15)
            try:
                await user.send(
                    f"⚠️ **Falta**: Reacción incorrecta en #🧵go-viral"
                )
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], faltas_dict[user.id]["estado"])
        elif str(reaction.emoji) == "🔥" and user == autor:
            await reaction.remove(user)
            faltas_dict[user.id]["faltas"] += 1
            faltas_dict[user.id]["ultima_falta_time"] = ahora
            advertencia = await reaction.message.channel.send(
                f"{user.mention} **No uses 🔥 en tu post**"
            )
            await advertencia.delete(delay=15)
            try:
                await user.send(
                    f"⚠️ **Falta**: 🔥 en tu propia publicación"
                )
            except:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], faltas_dict[user.id]["estado"])

@bot.event
async def on_member_remove(member):
    await registrar_log(f"👋 Miembro salió: {member.name}", categoria="miembros")

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

import atexit
atexit.register(save_state)

def run_webserver():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_webserver)
    t.daemon = True
    t.start()

# Iniciar el servidor web en un hilo separado
keep_alive()

# Iniciar el bot
bot.run(TOKEN)
