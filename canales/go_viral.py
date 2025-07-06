import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, REDIS_URL, EMOJIS_PERMITIDOS
from mensajes.viral_texto import (
    TITULO_FIJO, DESCRIPCION_FIJO, IMAGEN_URL,
    TITULO_SOLO_URL_EDU, DESCRIPCION_SOLO_URL_EDU
)
from datetime import datetime, timezone
import redis
import asyncio
import re
import hashlib
import aiohttp
from utils.logger import log_discord

async def validar_imagen_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=5) as resp:
                return resp.status == 200
    except Exception:
        return False

async def enviar_mensaje_con_reintento(canal, embed):
    for intento in range(5):
        try:
            return await canal.send(embed=embed)
        except discord.errors.HTTPException as e:
            if e.code == 429:
                wait_time = 2 ** intento
                await log_discord(None, f"Rate limiting detectado. Esperando {wait_time} segundos...", "warning")
                await asyncio.sleep(wait_time)
            else:
                await log_discord(None, f"Error inesperado al enviar mensaje: {e}", "error")
                break
    return None

def limpiar_url_tweet(texto):
    match = re.search(r"https?://x\.com/\w+/status/(\d+)", texto)
    if match:
        usuario = re.search(r"https?://x\.com/([^/]+)/status", texto)
        if usuario:
            user = usuario.group(1)
            status_id = match.group(1)
            return f"https://x.com/{user}/status/{status_id}"
    return None

def calcular_hash_embed(titulo, descripcion, imagen_url):
    contenido = f"{titulo}|{descripcion}|{imagen_url}"
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()

class GoViral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.tareas_ejecutadas = set()
        bot.loop.create_task(self.preload_historial_miembros())
        bot.loop.create_task(self.preload_apoyos_reacciones())
        bot.loop.create_task(self.init_mensaje_fijo())

    async def preload_historial_miembros(self):
        if 'preload_historial_miembros' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('preload_historial_miembros')

        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal.", "error")
            return

        await log_discord(self.bot, "🔍 [GO-VIRAL] Cargando historial...", "info")
        try:
            pipe = self.redis.pipeline()
            async for msg in canal.history(limit=1000, oldest_first=True):
                if msg.author.bot:
                    continue
                uid = str(msg.author.id)
                pipe.set(f"go_viral:primera_pub:{uid}", "1")
                pipe.set(f"go_viral:bienvenida:{uid}", "1")
                await asyncio.sleep(0.1)
            await pipe.execute()
            await log_discord(self.bot, "✅ [GO-VIRAL] Historial sincronizado.", "success")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error inesperado: {e}", "error")

    async def preload_apoyos_reacciones(self):
        if 'preload_apoyos_reacciones' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('preload_apoyos_reacciones')

        await self.bot.wait_until_ready()
        await asyncio.sleep(5)
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal.", "error")
            return

        await log_discord(self.bot, "🔄 [GO-VIRAL] Sincronizando reacciones...", "info")
        try:
            pipe = self.redis.pipeline()
            mensajes = [msg async for msg in canal.history(limit=1000, oldest_first=False)]
            for msg in mensajes:
                for reaction in msg.reactions:
                    if str(reaction.emoji) not in EMOJIS_PERMITIDOS:
                        async for user in reaction.users():
                            try:
                                await reaction.remove(user)
                            except Exception:
                                pass
                    elif str(reaction.emoji) == "🔥":
                        async for user in reaction.users():
                            if not user.bot:
                                pipe.sadd(f"go_viral:apoyos:{msg.id}", str(user.id))
                await asyncio.sleep(0.1)
            await pipe.execute()
            await log_discord(self.bot, "✅ [GO-VIRAL] Apoyos sincronizados.", "success")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error sincronizando reacciones: {e}", "error")

    async def init_mensaje_fijo(self):
        if 'init_mensaje_fijo' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('init_mensaje_fijo')

        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})", "error")
            return

        fecha = datetime.now().strftime("%Y-%m-%d")
        descripcion = DESCRIPCION_FIJO.format(fecha=fecha)
        imagen_url = IMAGEN_URL if await validar_imagen_url(IMAGEN_URL) else None
        hash_nuevo = calcular_hash_embed(TITULO_FIJO, descripcion, imagen_url)

        msg_id_guardado = self.redis.get("go_viral:mensaje_fijo_id")
        hash_guardado = self.redis.get("go_viral:mensaje_fijo_hash")

        if msg_id_guardado:
            try:
                mensaje = await canal.fetch_message(int(msg_id_guardado))
                if mensaje and mensaje.embeds:
                    embed_actual = mensaje.embeds[0]
                    hash_actual = calcular_hash_embed(
                        embed_actual.title or "",
                        embed_actual.description or "",
                        embed_actual.image.url if embed_actual.image else ""
                    )
                    if hash_actual == hash_nuevo:
                        await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo actualizado.", "success")
                        return
                    else:
                        embed_fijo = discord.Embed(
                            title=TITULO_FIJO,
                            description=descripcion,
                            color=discord.Color.blurple()
                        )
                        if imagen_url:
                            embed_fijo.set_image(url=imagen_url)
                        await mensaje.edit(embed=embed_fijo)
                        self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
                        await log_discord(self.bot, "🔄 [GO-VIRAL] Mensaje fijo actualizado.", "info")
                        return
                await mensaje.unpin()
            except Exception as e:
                await log_discord(self.bot, f"❌ [GO-VIRAL] Error inesperado: {e}", "error")

        embed_fijo = discord.Embed(
            title=TITULO_FIJO,
            description=descripcion,
            color=discord.Color.blurple()
        )
        if imagen_url:
            embed_fijo.set_image(url=imagen_url)
        msg = await enviar_mensaje_con_reintento(canal, embed_fijo)
        if msg:
            await msg.pin()
            self.redis.set("go_viral:mensaje_fijo_id", str(msg.id))
            self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
            await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo publicado.", "success")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return

        user_id = str(message.author.id)
        if self.redis.get(f"go_viral:override:{user_id}") == "1":
            await log_discord(self.bot, f"✅ [GO-VIRAL] {message.author} tiene override.", "info")
            return

        url = limpiar_url_tweet(message.content)
        if not url:
            try:
                await message.delete()
                embed = discord.Embed(
                    title=TITULO_SOLO_URL_EDU,
                    description=DESCRIPCION_SOLO_URL_EDU,
                    color=discord.Color.red()
                )
                await message.author.send(embed=embed)
                await log_discord(self.bot, f"❌ [GO-VIRAL] Mensaje de {message.author} eliminado: URL inválida.", "warning")
            except discord.errors.Forbidden:
                await log_discord(self.bot, f"❌ [GO-VIRAL] No se pudo eliminar mensaje o enviar DM a {message.author}.", "error")
            return

        await log_discord(self.bot, f"✅ [GO-VIRAL] Mensaje válido de {message.author}: {url}", "info")
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(GoViral(bot))
