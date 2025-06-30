# utils.py
import discord
import asyncio
from config import CANAL_LOGS, MAX_LOG_LENGTH, LOG_BATCH_DELAY
from discord_bot import bot
import logging

async def registrar_log(mensaje, categoria="bot"):
    try:
        canal_logs = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
        if canal_logs:
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
            await canal_logs.send(f"[{timestamp}] [{categoria.upper()}] {mensaje}")
            logging.info(f"Log registrado en {CANAL_LOGS}: {mensaje}")
        else:
            logging.warning(f"Canal de logs {CANAL_LOGS} no encontrado")
    except discord.Forbidden:
        logging.error(f"Permisos insuficientes para enviar log en {CANAL_LOGS}")
    except Exception as e:
        logging.error(f"Error al registrar log: {str(e)}")
        logging.error(traceback.format_exc())

async def publicar_mensaje_unico(canal, contenido, pinned=False):
    try:
        async for msg in canal.history(limit=100):
            if msg.author == bot.user and msg.content == contenido:
                if pinned and not msg.pinned:
                    await msg.pin()
                return msg
        msg = await canal.send(contenido)
        if pinned:
            await msg.pin()
        logging.info(f"Mensaje publicado en {canal.name}")
        return msg
    except discord.Forbidden:
        logging.error(f"Permisos insuficientes en {canal.name}")
        await registrar_log(f"Permisos insuficientes en {canal.name}", categoria="error")
    except Exception as e:
        logging.error(f"Error publicando mensaje en {canal.name}: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error publicando en {canal.name}: {str(e)}", categoria="error")

async def actualizar_mensaje_faltas(canal, member, faltas, aciertos, estado):
    try:
        mensaje_sistema = None
        async for msg in canal.history(limit=100):
            if msg.author == bot.user and msg.content.startswith("🚫 **FALTAS DE LOS USUARIOS**"):
                mensaje_sistema = msg
                break
        contenido = (
            f"🚫 **FALTAS DE LOS USUARIOS**\n\n"
            f"**Usuario**: {member.mention}\n"
            f"**Faltas**: {faltas}\n"
            f"**Aciertos**: {aciertos}\n"
            f"**Estado**: {estado}"
        )
        if mensaje_sistema:
            await mensaje_sistema.edit(content=contenido)
            logging.info(f"Mensaje de faltas editado en {canal.name} para {member.name}")
        else:
            mensaje_sistema = await canal.send(contenido)
            logging.info(f"Mensaje de faltas enviado en {canal.name} para {member.name}")
        return mensaje_sistema
    except discord.Forbidden:
        logging.error(f"Permisos insuficientes en {canal.name}")
        await registrar_log(f"Permisos insuficientes en {canal.name}", categoria="error")
    except Exception as e:
        logging.error(f"Error actualizando mensaje de faltas en {canal.name}: {str(e)}")
        logging.error(traceback.format_exc())
        await registrar_log(f"Error actualizando mensaje de faltas en {canal.name}: {str(e)}", categoria="error")

async def batch_log(log_batches):
    try:
        canal_logs = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
        if not canal_logs:
            logging.warning(f"Canal de logs {CANAL_LOGS} no encontrado")
            return
        
        for batch in log_batches:
            message = "\n".join(batch)
            if len(message) > MAX_LOG_LENGTH:
                messages = [message[i:i+MAX_LOG_LENGTH] for i in range(0, len(message), MAX_LOG_LENGTH)]
                for msg in messages:
                    await canal_logs.send(msg)
                    logging.info(f"Lote de logs enviado a {CANAL_LOGS}")
                    await asyncio.sleep(LOG_BATCH_DELAY)
            else:
                await canal_logs.send(message)
                logging.info(f"Lote de logs enviado a {CANAL_LOGS}")
                await asyncio.sleep(LOG_BATCH_DELAY)
    except discord.Forbidden:
        logging.error(f"Permisos insuficientes para enviar logs en {CANAL_LOGS}")
    except Exception as e:
        logging.error(f"Error al enviar logs en lote: {str(e)}")
        logging.error(traceback.format_exc())
