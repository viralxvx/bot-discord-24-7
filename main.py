import discord
import asyncio
import datetime
import atexit
import os
import traceback
from discord_bot import bot
from config import TOKEN, CANAL_OBJETIVO, CANAL_FALTAS, CANAL_REPORTES, CANAL_SOPORTE, CANAL_NORMAS_GENERALES, CANAL_ANUNCIOS, CANAL_LOGS, MENSAJE_NORMAS, MENSAJE_ANUNCIO_PERMISOS, MENSAJE_ACTUALIZACION_SISTEMA, FAQ_FALLBACK, CANAL_FLUJO_SOPORTE
from state_management import save_state, ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, faltas_dict, mensajes_recientes, faq_data, active_conversations
from utils import registrar_log, publicar_mensaje_unico, actualizar_mensaje_faltas, batch_log
import tasks
import commands
import message_handlers

# Verificar permisos de /data
try:
    print("="*50)
    print("Verificando permisos de /data")
    print("Contenido de /data:", os.listdir('/data'))
    print("Permisos de /data:", oct(os.stat('/data').st_mode)[-3:])
    print("="*50)
except Exception as e:
    print("Error al acceder a /data:", str(e))
    print("="*50)

# Registrar guardado de estado al salir
atexit.register(save_state)

# Iniciar servidor web
from app import keep_alive
keep_alive()

@bot.event
async def on_ready():
    try:
        print(f"Bot conectado como {bot.user} (Servidor siempre activo)")
        
        # Iniciar tareas programadas inmediatamente
        tasks.verificar_inactividad.start()
        tasks.resetear_faltas_diarias.start()
        tasks.clean_inactive_conversations.start()
        tasks.limpiar_mensajes_expulsados.start()
        
        # Lista para logs
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
        
        add_log(f"Bot iniciado en servidor siempre activo")
        
        procesos_exitosos = []
        
        # Solo inicializar si es la primera vez o después de actualizaciones importantes
        INITIAL_SETUP = True
        
        if INITIAL_SETUP:
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
                except Exception as e:
                    error_msg = f"Error en canal faltas: {str(e)}"
                    add_log(error_msg, "error")
                    print(error_msg)
                    print(traceback.format_exc())
            
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
                                elif line.startswith("**Respuesta:"):
                                    response = [line.replace("**Respuesta:**", "").strip()]
                                elif question and not line.startswith("**"):
                                    response.append(line.strip())
                            if question and response:
                                faq_data[question] = "\n".join(response)
                    procesos_exitosos.append("Carga FAQ")
                except Exception as e:
                    error_msg = f"Error cargando FAQ: {str(e)}"
                    add_log(error_msg, "error")
                    print(error_msg)
                    print(traceback.format_exc())
                    
            if not faq_data:
                faq_data.update(FAQ_FALLBACK)
                procesos_exitosos.append("FAQ por defecto")
            
            tasks_to_run = []
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    try:
                        if channel.name == CANAL_OBJETIVO:
                            tasks_to_run.append(publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True))
                            procesos_exitosos.append(f"Publicado #{CANAL_OBJETIVO}")
                        elif channel.name == CANAL_REPORTES:
                            content = (
                                "🔖 **Cómo Reportar Correctamente**:\n\n"
                                "1. **Menciona a un usuario** (ej. @Sharon) para reportar una infracción.\n"
                                "2. **Selecciona la infracción** del menú que aparecerá. ✅\n"
                                "3. Usa `!permiso <días>` para solicitar un **permiso de inactividad** (máx. 7 días).\n\n"
                                "El bot registrará el reporte en #📝logs."
                            )
                            tasks_to_run.append(publicar_mensaje_unico(channel, content, pinned=True))
                            procesos_exitosos.append(f"Publicado #{CANAL_REPORTES}")
                        elif channel.name == CANAL_SOPORTE:
                            content = "🔧 **Soporte Técnico**:\n\nEscribe **'Hola'** para abrir el menú de opciones. ✅"
                            tasks_to_run.append(publicar_mensaje_unico(channel, content, pinned=True))
                            procesos_exitosos.append(f"Publicado #{CANAL_SOPORTE}")
                        elif channel.name == CANAL_NORMAS_GENERALES:
                            tasks_to_run.append(publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True))
                            procesos_exitosos.append(f"Publicado #{CANAL_NORMAS_GENERALES}")
                        elif channel.name == CANAL_ANUNCIOS:
                            tasks_to_run.append(publicar_mensaje_unico(channel, MENSAJE_ANUNCIO_PERMISOS))
                            procesos_exitosos.append(f"Publicado #{CANAL_ANUNCIOS}")
                    except Exception as e:
                        error_msg = f"Error publicando en {channel.name}: {str(e)}"
                        add_log(error_msg, "error")
                        print(error_msg)
                        print(traceback.format_exc())
            
            # Ejecutar tareas en paralelo
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error en tarea {i}: {str(result)}")
        
        # Agregar logs de procesos
        if procesos_exitosos:
            add_log("Procesos completados: " + ", ".join(procesos_exitosos))
        
        # Enviar logs en batches
        if current_batch:
            log_batches.append(current_batch)
        
        if log_batches:
            await batch_log(log_batches)
    
    except Exception as e:
        print(f"Error crítico en on_ready: {str(e)}")
        print(traceback.format_exc())

@bot.event
async def on_member_join(member):
    try:
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
    except Exception as e:
        print(f"Error en on_member_join: {str(e)}")
        print(traceback.format_exc())

@bot.event
async def on_member_remove(member):
    try:
        await registrar_log(f"👋 Miembro salió: {member.name}", categoria="miembros")
    except Exception as e:
        print(f"Error en on_member_remove: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    bot.run(TOKEN)
