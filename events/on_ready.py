import asyncio
import datetime
from discord.ext import tasks
from handlers.anuncios import publicar_mensaje_unico
from handlers.normas_generales import MENSAJE_NORMAS
from handlers.reporte_incumplimiento import CANAL_REPORTES, CANAL_OBJETIVO, CANAL_SOPORTE, CANAL_NORMAS_GENERALES, CANAL_ANUNCIOS
from tasks.verificar_inactividad import verificar_inactividad
from tasks.clean_inactive import clean_inactive_conversations
from tasks.limpiar_expulsados import limpiar_mensajes_expulsados
from tasks.reset_faltas import resetear_faltas_diarias
from utils import add_log, batch_log

async def on_ready(bot):
    procesos_exitosos = []
    log_batches = []
    current_batch = []

    # Publicar mensajes únicos en canales específicos
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
                    content = (
                        "🔧 **Soporte Técnico**:\n\n"
                        "Escribe **'Hola'** para abrir el menú de opciones. ✅"
                    )
                    tasks_to_run.append(publicar_mensaje_unico(channel, content, pinned=True))
                    procesos_exitosos.append(f"Publicado #{CANAL_SOPORTE}")
                elif channel.name == CANAL_NORMAS_GENERALES:
                    tasks_to_run.append(publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True))
                    procesos_exitosos.append(f"Publicado #{CANAL_NORMAS_GENERALES}")
                elif channel.name == CANAL_ANUNCIOS:
                    from handlers.anuncios import MENSAJE_ANUNCIO_PERMISOS
                    tasks_to_run.append(publicar_mensaje_unico(channel, MENSAJE_ANUNCIO_PERMISOS))
                    procesos_exitosos.append(f"Publicado #{CANAL_ANUNCIOS}")
            except:
                pass

    await asyncio.gather(*tasks_to_run, return_exceptions=True)

    # Log de procesos exitosos
    if procesos_exitosos:
        add_log(f"Procesos completados: {', '.join(procesos_exitosos)}")

    # Ejecutar logs en batches si hay
    if current_batch:
        log_batches.append(current_batch)
    if log_batches:
        await batch_log(log_batches)

    # Iniciar tareas programadas
    verificar_inactividad.start()
    clean_inactive_conversations.start()
    limpiar_mensajes_expulsados.start()
    resetear_faltas_diarias.start()
