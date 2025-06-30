import discord
import re
import datetime
from discord.ext import commands
from handlers import go_viral, soporte, reporte_incumplimiento, anuncios, faltas, normas_generales, x_normas
from utils import save_state, actualizar_mensaje_faltas, registrar_log
from config import CANAL_LOGS, CANAL_FALTAS, CANAL_REPORTES, CANAL_SOPORTE, CANAL_OBJETIVO, CANAL_NORMAS_GENERALES, CANAL_X_NORMAS, CANAL_ANUNCIOS
from redis_database import mensajes_recientes, MAX_MENSAJES_RECIENTES, active_conversations, faltas_dict, ultima_publicacion_dict

async def on_message(bot: commands.Bot, message: discord.Message):
    if message.author.bot:
        return

    # Ignorar mensajes en canales de logs y faltas para evitar loops o spam
    if message.channel.name not in [CANAL_LOGS, CANAL_FALTAS]:
        canal_id = str(message.channel.id)
        mensaje_normalizado = message.content.strip().lower()
        if mensaje_normalizado:
            if any(mensaje_normalizado == msg.strip().lower() for msg in mensajes_recientes.get(canal_id, [])):
                try:
                    await message.delete()
                    try:
                        await message.author.send(f"⚠️ **Mensaje repetido eliminado** en #{message.channel.name}")
                    except:
                        pass
                except discord.Forbidden:
                    pass

            mensajes_recientes.setdefault(canal_id, []).append(message.content)
            if len(mensajes_recientes[canal_id]) > MAX_MENSAJES_RECIENTES:
                mensajes_recientes[canal_id].pop(0)

            await save_state()

    # Canal Reportes
    if message.channel.name == CANAL_REPORTES:
        await reporte_incumplimiento.handle_report(message, bot)

    # Canal Soporte
    elif message.channel.name == CANAL_SOPORTE:
        await soporte.handle_soporte(message, bot)

    # Canal Go Viral
    elif message.channel.name == CANAL_OBJETIVO:
        await go_viral.handle_go_viral(message, bot)

    # Canal Normas Generales
    elif message.channel.name == CANAL_NORMAS_GENERALES:
        await normas_generales.handle_normas_generales(message, bot)

    # Canal X Normas
    elif message.channel.name == CANAL_X_NORMAS:
        await x_normas.handle_x_normas(message, bot)

    # Canal Anuncios
    elif message.channel.name == CANAL_ANUNCIOS:
        await anuncios.handle_anuncios(message, bot)

    # Canal Faltas
    elif message.channel.name == CANAL_FALTAS:
        await faltas.handle_faltas(message, bot)

    await bot.process_commands(message)
