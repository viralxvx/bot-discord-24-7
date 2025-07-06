import discord
from discord.ext import commands, tasks
from config import CANAL_OBJETIVO_ID, REDIS_URL, EMOJIS_PERMITIDOS
from mensajes.viral_texto import *
from datetime import datetime, timedelta
import redis
import asyncio
import re
import hashlib
import aiohttp
from utils.logger import log_discord
from canales.faltas import registrar_falta

async def validar_imagen_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=5) as resp:
                return resp.status == 200
    except Exception:
        return False

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

    # -- HISTORIAL DE MIEMBROS Y REACCIONES INICIALES --
    async def preload_historial_miembros(self):
        if 'preload_historial_miembros' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('preload_historial_miembros')
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal.", "error", scope="go_viral")
            return
        await log_discord(self.bot, "🔍 [GO-VIRAL] Cargando historial...", "info", scope="go_viral")
        try:
            async for msg in canal.history(limit=1000, oldest_first=True):
                if msg.author.bot:
                    continue
                uid = str(msg.author.id)
                self.redis.set(f"go_viral:primera_pub:{uid}", "1")
                self.redis.set(f"go_viral:bienvenida:{uid}", "1")
                await asyncio.sleep(0.1)
            await log_discord(self.bot, "✅ [GO-VIRAL] Historial sincronizado.", "success", scope="go_viral")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error inesperado: {e}", "error", scope="go_viral")

    async def preload_apoyos_reacciones(self):
        if 'preload_apoyos_reacciones' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('preload_apoyos_reacciones')
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal.", "error", scope="go_viral")
            return
        await log_discord(self.bot, "🔄 [GO-VIRAL] Sincronizando reacciones...", "info", scope="go_viral")
        try:
            async for msg in canal.history(limit=1000, oldest_first=False):
                for reaction in msg.reactions:
                    if str(reaction.emoji) not in EMOJIS_PERMITIDOS:
                        async for user in reaction.users():
                            try:
                                await reaction.remove(user)
                            except Exception:
                                pass
            await log_discord(self.bot, "✅ [GO-VIRAL] Apoyos sincronizados.", "success", scope="go_viral")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error sincronizando reacciones: {e}", "error", scope="go_viral")

    async def init_mensaje_fijo(self):
        if 'init_mensaje_fijo' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('init_mensaje_fijo')
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})", "error", scope="go_viral")
            return
        fecha = datetime.now().strftime("%Y-%m-%d")
        descripcion = DESCRIPCION_FIJO.format(fecha=fecha)
        imagen_url = IMAGEN_URL if await validar_imagen_url(IMAGEN_URL) else None
        hash_nuevo = calcular_hash_embed(TITULO_FIJO, descripcion, imagen_url)
        msg_id_guardado = self.redis.get("go_viral:mensaje_fijo_id")
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
                        await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo actualizado.", "success", scope="go_viral")
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
                        await log_discord(self.bot, "🔄 [GO-VIRAL] Mensaje fijo actualizado.", "info", scope="go_viral")
                        return
                await mensaje.unpin()
            except Exception as e:
                await log_discord(self.bot, f"❌ [GO-VIRAL] Error inesperado: {e}", "error", scope="go_viral")
        embed_fijo = discord.Embed(
            title=TITULO_FIJO,
            description=descripcion,
            color=discord.Color.blurple()
        )
        if imagen_url:
            embed_fijo.set_image(url=imagen_url)
        msg = await canal.send(embed=embed_fijo)
        if msg:
            await msg.pin()
            self.redis.set("go_viral:mensaje_fijo_id", str(msg.id))
            self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
            await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo publicado.", "success", scope="go_viral")

    # ------------------------- LISTENER PRINCIPAL -------------------------

    @commands.Cog.listener()
    async def on_message(self, message):
        # SOLO CANAL OBJETIVO Y MENSAJE DE USUARIO NORMAL
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return
        user_id = str(message.author.id)

        # CHEQUEO BLOQUEO (falta)
        if self.redis.get(f"go_viral:bloqueado:{user_id}"):
            await message.delete()
            await registrar_falta(user_id, "Intento de publicar estando bloqueado")
            return

        # SOLO PERMITIR ENLACE LIMPIO
        url_limpio = limpiar_url_tweet(message.content)
        if not url_limpio:
            # Esperar 15s, borrar, enviar DM educativo, sumar falta
            await asyncio.sleep(15)
            try:
                await message.delete()
                embed = discord.Embed(
                    title=TITULO_SOLO_URL_EDU,
                    description=DESCRIPCION_SOLO_URL_EDU.format(usuario=message.author.mention),
                    color=discord.Color.red()
                )
                await message.author.send(embed=embed)
                await registrar_falta(user_id, "Publicar mensaje no permitido")
                await log_discord(self.bot, f"❌ [GO-VIRAL] Mensaje de {message.author} eliminado: URL inválida.", "warning", scope="go_viral")
            except Exception:
                pass
            return

        # SI ES PRIMERA PUBLICACIÓN DEL USUARIO
        if not self.redis.get(f"go_viral:primera_pub:{user_id}"):
            self.redis.set(f"go_viral:primera_pub:{user_id}", "1")
            embed = discord.Embed(
                title=TITULO_BIENVENIDA,
                description=DESCRIPCION_BIENVENIDA,
                color=discord.Color.green()
            )
            await message.author.send(embed=embed)
            await log_discord(self.bot, f"🎉 [GO-VIRAL] Bienvenida enviada a {message.author}.", "info", scope="go_viral")

        # CHEQUEO DE TURNO (dos publicaciones ajenas o 24h)
        if not await self.check_intervalo(message):
            try:
                await message.delete()
                embed = discord.Embed(
                    title=TITULO_INTERVALO_EDU,
                    description=DESCRIPCION_INTERVALO_EDU.format(usuario=message.author.mention),
                    color=discord.Color.orange()
                )
                await message.author.send(embed=embed)
                await registrar_falta(user_id, "No respetar intervalo de publicaciones")
            except Exception:
                pass
            return

        # CHEQUEO DE APOYO A ANTERIORES (🔥 hasta 9)
        if not await self.check_apoyos_anteriores(message):
            try:
                await message.delete()
                embed = discord.Embed(
                    title=TITULO_APOYO_9_EDU,
                    description=DESCRIPCION_APOYO_9_EDU.format(usuario=message.author.mention),
                    color=discord.Color.orange()
                )
                await message.author.send(embed=embed)
                await registrar_falta(user_id, "No apoyar publicaciones anteriores")
            except Exception:
                pass
            return

        # INICIA TAREA DE CHEQUEO 👍 EN 2 MINUTOS
        self.bot.loop.create_task(self.validar_like(message))

        # REGISTRO DE PUBLICACIÓN VÁLIDA EN HISTORIAL (para control futuro)
        self.redis.set(f"go_viral:last_post:{user_id}", str(message.id))
        self.redis.set(f"go_viral:last_post_time:{user_id}", str(datetime.now().timestamp()))

        await log_discord(self.bot, f"✅ [GO-VIRAL] Mensaje válido de {message.author}: {url_limpio}", "info", scope="go_viral")

    # -- CHEQUEO INTERVALO ENTRE PUBLICACIONES --
    async def check_intervalo(self, message):
        user_id = str(message.author.id)
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        last_time = self.redis.get(f"go_viral:last_post_time:{user_id}")
        if not last_time:
            return True  # Primera vez
        last_time = float(last_time)
        now = datetime.now().timestamp()
        if (now - last_time) >= 24*3600:
            return True  # Pasaron 24h

        # Verificar dos publicaciones válidas de otros
        count = 0
        async for msg in canal.history(limit=100, after=datetime.fromtimestamp(last_time)):
            if msg.author.id != message.author.id and limpiar_url_tweet(msg.content):
                count += 1
            if count >= 2:
                return True
        return False

    # -- CHEQUEO DE APOYO (🔥) A LOS ANTERIORES HASTA 9 --
    async def check_apoyos_anteriores(self, message):
        user_id = str(message.author.id)
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        last_msg_id = self.redis.get(f"go_viral:last_post:{user_id}")
        msgs = []
        found = False
        async for msg in canal.history(limit=100, oldest_first=False):
            if str(msg.author.id) == user_id:
                if msg.id == int(message.id):  # No contar el mensaje actual
                    continue
                found = True
                break
            if limpiar_url_tweet(msg.content):
                msgs.append(msg)
            if len(msgs) >= 9:
                break
        # Revisar que el usuario haya puesto 🔥 en todos los encontrados
        for post in msgs:
            try:
                reaction = discord.utils.get(post.reactions, emoji="🔥")
                if not reaction:
                    return False
                users = [u async for u in reaction.users()]
                if int(user_id) not in [u.id for u in users]:
                    return False
            except Exception:
                return False
        return True

    # -- TAREA: CHEQUEO DE 👍 DEL AUTOR EN 2 MINUTOS --
    async def validar_like(self, message):
        user_id = message.author.id
        await asyncio.sleep(120)
        msg = None
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        try:
            msg = await canal.fetch_message(message.id)
        except Exception:
            return  # Ya fue borrado
        if msg:
            reaction = discord.utils.get(msg.reactions, emoji="👍")
            if reaction:
                users = [u async for u in reaction.users()]
                if user_id in [u.id for u in users]:
                    return  # Sí reaccionó correctamente
            try:
                await msg.delete()
                embed = discord.Embed(
                    title=TITULO_SIN_LIKE_EDU,
                    description=DESCRIPCION_SIN_LIKE_EDU.format(usuario=msg.author.mention),
                    color=discord.Color.red()
                )
                await msg.author.send(embed=embed)
                await registrar_falta(user_id, "No validar publicación con 👍 en 2 minutos")
            except Exception:
                pass

    # -- REACCIONES SOLO PERMITIDAS Y 🔥 PROPIO POST --
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.channel.id != CANAL_OBJETIVO_ID:
            return
        # Solo se permiten 🔥 y 👍
        if str(reaction.emoji) not in EMOJIS_PERMITIDOS:
            try:
                await reaction.remove(user)
                embed = discord.Embed(
                    title=TITULO_SOLO_REACCION_EDU,
                    description=DESCRIPCION_SOLO_REACCION_EDU.format(usuario=user.mention),
                    color=discord.Color.red()
                )
                await user.send(embed=embed)
                await registrar_falta(user.id, "Reacción no permitida")
            except Exception:
                pass
        # Prohibido 🔥 en propio post
        if str(reaction.emoji) == "🔥" and user.id == reaction.message.author.id:
            try:
                await reaction.remove(user)
                embed = discord.Embed(
                    title="🔥 Prohibido 🔥 en tu propio post",
                    description="No puedes poner 🔥 en tu propio post.",
                    color=discord.Color.orange()
                )
                await user.send(embed=embed)
                await registrar_falta(user.id, "Usar 🔥 en propio post")
            except Exception:
                pass

    # -- CHEQUEO SI EL USUARIO BORRA SU MENSAJE (SUMA FALTA) --
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id != CANAL_OBJETIVO_ID:
            return
        if message.author.bot:
            return
        await registrar_falta(message.author.id, "Borrar publicación del canal go-viral")

async def setup(bot):
    await bot.add_cog(GoViral(bot))
