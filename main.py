import logging
import discord
import asyncio
import datetime
import atexit
import os
import traceback

# CONFIGURACIÓN DE LOGGING
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)  # Solo muestra WARNINGS y ERRORES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from discord_bot import bot
from config import TOKEN, CANAL_OBJETIVO, CANAL_FALTAS, CANAL_REPORTES, CANAL_SOPORTE, CANAL_NORMAS_GENERALES, CANAL_ANUNCIOS, CANAL_LOGS, MENSAJE_NORMAS, MENSAJE_ANUNCIO_PERMISOS, MENSAJE_ACTUALIZACION_SISTEMA, FAQ_FALLBACK, CANAL_FLUJO_SOPORTE
from state_management import save_state, load_state, ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, faltas_dict, mensajes_recientes, faq_data, active_conversations, init_db
from utils import registrar_log, publicar_mensaje_unico, actualizar_mensaje_faltas, batch_log
import tasks
import commands
import message_handlers

# Verificar permisos de /data
try:
    logging.info("="*50)
    logging.info("Verificando permisos de /data")
    logging.info(f"Contenido de /data: {os.listdir('/data')}")
    logging.info(f"Permisos de /data: {oct(os.stat('/data').st_mode)[-3:]}")
    logging.info("="*50)
except Exception as e:
    logging.error(f"Error al acceder a /data: {str(e)}")
    logging.info("="*50)

# Registrar guardado de estado al salir
atexit.register(save_state)

@bot.event
async def on_ready():
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
    
    try:
        logging.info(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
        add_log(f"Bot iniciado en servidor siempre activo")
        
        # Inicializar la conexión a Redis
        logging.info("Iniciando conexión a Redis...")
        await init_db()
        logging.info("Conexión a Redis completada")
        
        # Cargar el estado desde Redis
        logging.info("Cargando estado desde Redis...")
        await load_state()
        logging.info("Estado cargado correctamente")
        
        # Iniciar tareas programadas
        logging.info("Iniciando tareas programadas...")
        tasks.verificar_inactividad.start()
        tasks.resetear_faltas_diarias.start()
        tasks.clean_inactive_conversations.start()
        tasks.limpiar_mensajes_expulsados.start()
        logging.info("Tareas programadas iniciadas")
        
        procesos_exitosos = []
        INITIAL_SETUP = True
        
        if INITIAL_SETUP:
            logging.info("Iniciando configuración inicial de canales...")
            for guild in bot.guilds:
                logging.info(f"Procesando servidor: {guild.name} (ID: {guild.id})")
                for channel in guild.text_channels:
                    logging.info(f"Verificando canal: {channel.name} (ID: {channel.id})")
                    try:
                        if channel.name == CANAL_FALTAS:
                            logging.info(f"Configurando canal {CANAL_FALTAS}...")
                            mensaje_sistema = None
                            async for msg in channel.history(limit=100):
                                if msg.author == bot.user and msg.content.startswith("🚫 **FALTAS DE LOS USUARIOS**"):
                                    mensaje_sistema = msg
                                    break
                            if mensaje_sistema:
                                if mensaje_sistema.content != MENSAJE_ACTUALIZACION_SISTEMA:
                                    await mensaje_sistema.edit(content=MENSAJE_ACTUALIZACION_SISTEMA)
                                    logging.info(f"Mensaje de faltas editado en {CANAL_FALTAS}")
                            else:
                                mensaje_sistema = await channel.send(MENSAJE_ACTUALIZACION_SISTEMA)
                                logging.info(f"Mensaje de faltas enviado en {CANAL_FALTAS}")
                            procesos_exitosos.append("Mensaje sistema faltas")
                        
                        elif channel.name == CANAL_FLUJO_SOPORTE:
                            logging.info(f"Configurando canal {CANAL_FLUJO_SOPORTE}...")
                            async for msg in channel.history(limit=100):
                                if msg.author == bot.user and msg.pinned:
                                    lines = msg.content.split("\n")
                                    question = None
                                    response = []
                                    for line in lines:
                                        if line.startswith("**Pregunta:"):
                                            question = line.replace("**Pregunta:**", "").strip()
                                        elif line.startswith("**Respuesta:"):
                                            response = [line.replace("**Respuesta:**", "").strip()]
                                        elif question and not line.startswith("**"):
                                            response.append(line.strip())
                                    if question and response:
                                        faq_data[question] = "\n".join(response)
                            procesos_exitosos.append("Carga FAQ")
                            logging.info(f"FAQ cargado desde {CANAL_FLUJO_SOPORTE}")
                        
                        elif channel.name == CANAL_OBJETIVO:
                            await publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True)
                            procesos_exitosos.append(f"Publicado #{CANAL_OBJETIVO}")
                            logging.info(f"Mensaje publicado en {CANAL_OBJETIVO}")
                        elif channel.name == CANAL_REPORTES:
                            content = (
                                "🔖 **Cómo Reportar Correctamente**:\n\n"
                                "1. **Menciona a un usuario** (ej. @Sharon) para reportar una infracción.\n"
                                "2. **Selecciona la infracción** del menú que aparecerá. ✅\n"
                                "3. Usa `!permiso <días>` para solicitar un **permiso de inactividad** (máx. 7 días).\n\n"
                                "El bot registrará el reporte en #📝logs."
                            )
                            await publicar_mensaje_unico(channel, content, pinned=True)
                            procesos_exitosos.append(f"Publicado #{CANAL_REPORTES}")
                            logging.info(f"Mensaje publicado en {CANAL_REPORTES}")
                        elif channel.name == CANAL_SOPORTE:
                            content = "🔧 **Soporte Técnico**:\n\nEscribe **'Hola'** para abrir el menú de opciones. ✅"
                            await publicar_mensaje_unico(channel, content, pinned=True)
                            procesos_exitosos.append(f"Publicado #{CANAL_SOPORTE}")
                            logging.info(f"Mensaje publicado en {CANAL_SOPORTE}")
                        elif channel.name == CANAL_NORMAS_GENERALES:
                            await publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True)
                            procesos_exitosos.append(f"Publicado #{CANAL_NORMAS_GENERALES}")
                            logging.info(f"Mensaje publicado en {CANAL_NORMAS_GENERALES}")
                        elif channel.name == CANAL_ANUNCIOS:
                            await publicar_mensaje_unico(channel, MENSAJE_ANUNCIO_PERMISOS)
                            procesos_exitosos.append(f"Publicado #{CANAL_ANUNCIOS}")
                            logging.info(f"Mensaje publicado en {CANAL_ANUNCIOS}")
                    
                    except discord.Forbidden as e:
                        logging.error(f"Permisos insuficientes en {channel.name}: {str(e)}")
                        add_log(f"Permisos insuficientes en {channel.name}: {str(e)}", "error")
                    except Exception as e:
                        logging.error(f"Error publicando en {channel.name}: {str(e)}")
                        logging.error(traceback.format_exc())
                        add_log(f"Error publicando en {channel.name}: {str(e)}", "error")
            
            if not faq_data:
                faq_data.update(FAQ_FALLBACK)
                procesos_exitosos.append("FAQ por defecto")
                logging.info("FAQ por defecto cargado")
        
        if procesos_exitosos:
            add_log("Procesos completados: " + ", ".join(procesos_exitosos))
            logging.info(f"Procesos completados: {', '.join(procesos_exitosos)}")
        
        if current_batch:
            log_batches.append(current_batch)
        
        if log_batches:
            await batch_log(log_batches)
            logging.info("Logs enviados al canal de logs")
        
        logging.info("Inicialización completada exitosamente")
    
    except Exception as e:
        logging.error(f"Error crítico en on_ready: {str(e)}")
        logging.error(traceback.format_exc())
        add_log(f"Error crítico en on_ready: {str(e)}", "error")

@bot.event
async def on_member_join(member):
    try:
        logging.info(f"Nuevo miembro: {member.name} (ID: {member.id})")
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
                logging.info(f"Mensaje de bienvenida enviado en {canal_presentate.name}")
            except discord.Forbidden:
                logging.error(f"Permisos insuficientes en {canal_presentate.name}")
                await registrar_log(f"Permisos insuficientes en {canal_presentate.name}", categoria="error")
        
        if canal_faltas:
            try:
                if str(member.id) not in faltas_dict:
                    faltas_dict[str(member.id)] = {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
                await actualizar_mensaje_faltas(canal_faltas, member, 0, 0, "OK")
                logging.info(f"Estado de faltas actualizado para {member.name} en {canal_faltas.name}")
            except discord.Forbidden:
                logging.error(f"Permisos insuficientes en {canal_faltas.name}")
                await registrar_log(f"Permisos insuficientes en {canal_faltas.name}", categoria="error")
                
        await registrar_log(f"👤 Nuevo miembro: {member.name}", categoria="miembros")
        logging.info(f"Log de nuevo miembro registrado: {member.name}")
    except Exception as e:
        logging.error(f"Error en on_member_join: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error en on_member_join: {str(e)}", categoria="error")

@bot.event
async def on_member_remove(member):
    try:
        await registrar_log(f"👋 Miembro salió: {member.name}", categoria="miembros")
        logging.info(f"Log de miembro saliente registrado: {member.name}")
    except Exception as e:
        logging.error(f"Error en on_member_remove: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error en on_member_remove: {str(e)}", categoria="error")

if __name__ == "__main__":
    try:
        logging.info("Iniciando bot...")
        bot.run(TOKEN)
    except Exception as e:
        logging.error(f"Error al iniciar el bot: {str(e)}")
        logging.error(traceback.format_exc())
