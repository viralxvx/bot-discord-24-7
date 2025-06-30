# tasks.py
import discord
from discord.ext import tasks
import datetime
from config import CANAL_OBJETIVO, CANAL_FALTAS, INACTIVITY_TIMEOUT, CANAL_SOPORTE
from state_management import ultima_publicacion_dict, faltas_dict, permisos_inactividad, active_conversations
from utils import actualizar_mensaje_faltas, registrar_log
import logging

@tasks.loop(hours=24)
async def verificar_inactividad():
    try:
        logging.info("Iniciando tarea de verificación de inactividad...")
        guild = discord.utils.get(bot.guilds, id=1346959710519038003)  # ID del servidor Viral 𝕏 | V𝕏
        if not guild:
            logging.error("Servidor no encontrado para verificar inactividad")
            await registrar_log("Servidor no encontrado para verificar inactividad", categoria="error")
            return

        canal_faltas = discord.utils.get(guild.text_channels, name=CANAL_FALTAS)
        if not canal_faltas:
            logging.error(f"Canal {CANAL_FALTAS} no encontrado")
            await registrar_log(f"Canal {CANAL_FALTAS} no encontrado", categoria="error")
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        for member in guild.members:
            if member.bot:
                continue
            user_id = str(member.id)
            if user_id in permisos_inactividad and permisos_inactividad[user_id]:
                continue
            last_post = ultima_publicacion_dict.get(user_id, now)
            days_inactive = (now - last_post).days
            if days_inactive >= INACTIVITY_TIMEOUT:
                faltas_dict[user_id]["faltas"] += 1
                faltas_dict[user_id]["ultima_falta_time"] = now
                faltas_dict[user_id]["estado"] = "INACTIVO"
                await actualizar_mensaje_faltas(canal_faltas, member, faltas_dict[user_id]["faltas"], faltas_dict[user_id]["aciertos"], "INACTIVO")
                await registrar_log(f"Usuario {member.name} marcado como inactivo (faltas: {faltas_dict[user_id]['faltas']})", categoria="inactividad")
        logging.info("Tarea de verificación de inactividad completada")
    except Exception as e:
        logging.error(f"Error en verificar_inactividad: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error en verificar_inactividad: {str(e)}", categoria="error")

@tasks.loop(hours=24)
async def resetear_faltas_diarias():
    try:
        logging.info("Iniciando tarea de reseteo de faltas diarias...")
        guild = discord.utils.get(bot.guilds, id=1346959710519038003)
        if not guild:
            logging.error("Servidor no encontrado para resetear faltas")
            await registrar_log("Servidor no encontrado para resetear faltas", categoria="error")
            return

        canal_faltas = discord.utils.get(guild.text_channels, name=CANAL_FALTAS)
        if not canal_faltas:
            logging.error(f"Canal {CANAL_FALTAS} no encontrado")
            await registrar_log(f"Canal {CANAL_FALTAS} no encontrado", categoria="error")
            return

        for user_id in faltas_dict:
            member = guild.get_member(int(user_id))
            if member:
                faltas_dict[user_id]["faltas"] = 0
                faltas_dict[user_id]["estado"] = "OK"
                await actualizar_mensaje_faltas(canal_faltas, member, 0, faltas_dict[user_id]["aciertos"], "OK")
                await registrar_log(f"Faltas reseteadas para {member.name}", categoria="reset")
        logging.info("Tarea de reseteo de faltas diarias completada")
    except Exception as e:
        logging.error(f"Error en resetear_faltas_diarias: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error en resetear_faltas_diarias: {str(e)}", categoria="error")

@tasks.loop(hours=24)
async def clean_inactive_conversations():
    try:
        logging.info("Iniciando tarea de limpieza de conversaciones inactivas...")
        now = datetime.datetime.now(datetime.timezone.utc)
        expired = []
        for user_id, data in active_conversations.items():
            last_interaction = data.get("last_interaction")
            if last_interaction and (now - datetime.datetime.fromisoformat(last_interaction)).days > 1:
                expired.append(user_id)
        for user_id in expired:
            del active_conversations[user_id]
        if expired:
            await registrar_log(f"Limpiadas {len(expired)} conversaciones inactivas", categoria="limpieza")
        logging.info("Tarea de limpieza de conversaciones inactivas completada")
    except Exception as e:
        logging.error(f"Error en clean_inactive_conversations: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error en clean_inactive_conversations: {str(e)}", categoria="error")

@tasks.loop(hours=24)
async def limpiar_mensajes_expulsados():
    try:
        logging.info("Iniciando tarea de limpieza de mensajes de usuarios expulsados...")
        guild = discord.utils.get(bot.guilds, id=1346959710519038003)
        if not guild:
            logging.error("Servidor no encontrado para limpiar mensajes")
            await registrar_log("Servidor no encontrado para limpiar mensajes", categoria="error")
            return

        canal_objetivo = discord.utils.get(guild.text_channels, name=CANAL_OBJETIVO)
        if not canal_objetivo:
            logging.error(f"Canal {CANAL_OBJETIVO} no encontrado")
            await registrar_log(f"Canal {CANAL_OBJETIVO} no encontrado", categoria="error")
            return

        for user_id in list(faltas_dict.keys()):
            member = guild.get_member(int(user_id))
            if not member:
                async for msg in canal_objetivo.history(limit=100):
                    if str(msg.author.id) == user_id:
                        await msg.delete()
                del faltas_dict[user_id]
                await registrar_log(f"Mensajes de usuario {user_id} eliminados y datos de faltas borrados", categoria="limpieza")
        logging.info("Tarea de limpieza de mensajes de usuarios expulsados completada")
    except Exception as e:
        logging.error(f"Error en limpiar_mensajes_expulsados: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error en limpiar_mensajes_expulsados: {str(e)}", categoria="error")
