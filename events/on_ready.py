import logging
import discord
import asyncio
import datetime
import traceback
from config import (
    CANAL_OBJETIVO, CANAL_FALTAS, CANAL_REPORTES, 
    CANAL_SOPORTE, CANAL_NORMAS_GENERALES, CANAL_ANUNCIOS, 
    MENSAJE_NORMAS, MENSAJE_ANUNCIO_PERMISOS, 
    MENSAJE_ACTUALIZACION_SISTEMA, FAQ_FALLBACK, 
    CANAL_FLUJO_SOPORTE
)
from state_management import faq_data, faltas_dict
from utils import publicar_mensaje_unico, batch_log, registrar_log
from tasks.verificar_inactividad import verificar_inactividad
from tasks.reset_faltas import resetear_faltas_diarias
from tasks.clean_inactive import clean_inactive_conversations
from tasks.limpiar_expulsados import limpiar_mensajes_expulsados

async def handle_on_ready(bot):
    try:
        print(f"Bot conectado como {bot.user} (Servidor siempre activo)")
        
        # Iniciar tareas programadas
        verificar_inactividad.start()
        resetear_faltas_diarias.start()
        clean_inactive_conversations.start()
        limpiar_mensajes_expulsados.start()
        
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
            # Inicialización de canales
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
            
            # Cargar FAQ
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
                    
            if not faq_data:
                faq_data.update(FAQ_FALLBACK)
                procesos_exitosos.append("FAQ por defecto")
            
            # Publicar mensajes en canales
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
