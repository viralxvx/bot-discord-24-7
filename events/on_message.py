import re
import discord
from config import (
    CANAL_LOGS, CANAL_FALTAS, CANAL_REPORTES, CANAL_SOPORTE, 
    CANAL_OBJETIVO, CANAL_NORMAS_GENERALES, CANAL_X_NORMAS, 
    CANAL_ANUNCIOS, MAX_MENSAJES_RECIENTES, MENSAJE_NORMAS
)
from state_management import (
    ultima_publicacion_dict, faltas_dict, save_state, 
    active_conversations, mensajes_recientes
)
from utils import (
    actualizar_mensaje_faltas, registrar_log, 
    publicar_mensaje_unico
)
# Importación corregida usando rutas relativas
from views.report_menu import ReportMenu
from views.support_menu import SupportMenu
from handlers import (
    go_viral, reporte_incumplimiento, 
    soporte, normas_generales
)

async def handle_on_message(bot, message):
    # Manejo de mensajes repetidos
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
    
    # Router de mensajes por canal
    try:
        if message.channel.name == CANAL_OBJETIVO and not message.author.bot:
            await go_viral.handle_go_viral_message(message)
            
        elif message.channel.name == CANAL_REPORTES and not message.author.bot:
            await reporte_incumplimiento.handle_reporte_message(message)
            
        elif message.channel.name == CANAL_SOPORTE and not message.author.bot:
            await soporte.handle_soporte_message(message)
            
        elif message.channel.name in [CANAL_NORMAS_GENERALES, CANAL_X_NORMAS] and not message.author.bot:
            await normas_generales.handle_normas_message(message)
            
    except Exception as e:
        print(f"Error en on_message: {str(e)}")
    
    await bot.process_commands(message)
