import discord
from discord.ext import commands
import re
import asyncio
import traceback
import logging
import time
from datetime import datetime
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_OBJETIVO, CANAL_LOGS

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('go_viral_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

mensaje_reglas_actual = None

async def enviar_reglas_canal(bot):
    global mensaje_reglas_actual

    try:
        canal = bot.get_channel(CANAL_OBJETIVO)
        if not canal:
            logger.error("Canal no encontrado.")
            return False

        permisos = canal.permissions_for(canal.guild.me)
        if not permisos.send_messages or not permisos.embed_links:
            logger.error("Faltan permisos para enviar mensajes o embeds.")
            return False

        logger.debug("Buscando mensajes anteriores del bot para eliminar...")
        async for msg in canal.history(limit=50):
            if msg.author == bot.user and msg.embeds:
                try:
                    await msg.unpin()
                    await msg.delete()
                    logger.debug(f"Mensaje {msg.id} eliminado y desanclado.")
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error al eliminar/desanclar mensaje {msg.id}: {e}")

        embed = discord.Embed(
            title="Bienvenidos",
            description="Esto es una prueba",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"🟢 BOT ONLINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        logger.debug("Enviando mensaje de bienvenida...")
        mensaje = await canal.send(embed=embed)
        logger.debug(f"Mensaje enviado con ID: {mensaje.id}")
        await mensaje.pin()
        logger.debug(f"Mensaje {mensaje.id} anclado.")
 mensaje_reglas_actual = mensaje

        try:
            RedisState().set_welcome_message_id(mensaje.id, CANAL_OBJETIVO)
            logger.debug("ID del mensaje guardado en Redis.")
        except Exception as e:
            logger.warning(f"Redis error: {e}")

        await registrar_log(
            f"✅ Mensaje de bienvenida publicado y fijado (embed)",
            bot.user,
            canal
        )

        logger.info("✅ Mensaje de bienvenida enviado correctamente como embed.")
        return True

    except Exception as e:
        logger.error(f"Error en enviar_reglas_canal: {e}")
        logger.error(traceback.format_exc())
        return False

async def cleanup_on_disconnect(bot):
    global mensaje_reglas_actual
    try:
        if mensaje_reglas_actual:
            canal = bot.get_channel(CANAL_OBJETIVO)
            if canal:
                try:
                    embed = mensaje_reglas_actual.embeds[0]
                    embed.set_footer(text="🔴 BOT OFFLINE")
                    await mensaje_reglas_actual.edit(embed=embed)
                except:
                    pass

                try:
                    await mensaje_reglas_actual.unpin()
                except:
                    pass

        try:
            RedisState().clear_welcome_message_id(CANAL_OBJETIVO)
        except:
            pass
    except Exception as e:
        logger.error(f"Error en cleanup: {e}")

def setup(bot):
    @bot.event
    async def on_ready():
        logger.info(f'BOT CONECTADO: {bot.user}')
        await enviar_reglas_canal(bot)

    @bot.event
    async def on_disconnect():
        await cleanup_on_disconnect(bot)

    @bot.event
    async def on_resumed():
        await enviar_reglas_canal(bot)

    @bot.command(name='debug_welcome')
    @commands.has_permissions(administrator=True)
    async def debug_welcome(ctx):
        await ctx.send("🔍 Iniciando debugging... Revisa los logs", delete_after=5)
        success = await enviar_reglas_canal(bot)
        await ctx.send("✅ Debug completado" if success else "❌ Debug fallido", delete_after=10)

    @bot.event
    async def on_message(message):
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
            await bot.process_commands(message)
            return
        await bot.process_commands(message)

    @bot.event
    async def on_reaction_add(reaction, user):
        pass  # Código para manejo de reacciones aquí
