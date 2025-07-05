import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, REDIS_URL
from mensajes.viral_texto import (
    TITULO_FIJO, DESCRIPCION_FIJO, IMAGEN_URL,
    TITULO_BIENVENIDA, DESCRIPCION_BIENVENIDA,
    TITULO_URL_EDU, DESCRIPCION_URL_EDU,
    TITULO_URL_DM, DESCRIPCION_URL_DM,
    TITULO_SIN_LIKE_EDU, DESCRIPCION_SIN_LIKE_EDU,
    TITULO_SIN_LIKE_DM, DESCRIPCION_SIN_LIKE_DM,
    TITULO_APOYO_9_EDU, DESCRIPCION_APOYO_9_EDU,
    TITULO_APOYO_9_DM, DESCRIPCION_APOYO_9_DM,
    TITULO_INTERVALO_EDU, DESCRIPCION_INTERVALO_EDU,
    TITULO_INTERVALO_DM, DESCRIPCION_INTERVALO_DM,
    TITULO_SOLO_URL_EDU, DESCRIPCION_SOLO_URL_EDU,
    TITULO_SOLO_URL_DM, DESCRIPCION_SOLO_URL_DM,
    TITULO_SOLO_REACCION_EDU, DESCRIPCION_SOLO_REACCION_EDU,
    TITULO_SOLO_REACCION_DM, DESCRIPCION_SOLO_REACCION_DM
)
from datetime import datetime, timezone
import redis
import asyncio
import re
import hashlib
from utils.logger import log_discord  # 👈 IMPORTANTE

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
        bot.loop.create_task(self.preload_historial_miembros())
        bot.loop.create_task(self.preload_apoyos_reacciones())
        bot.loop.create_task(self.init_mensaje_fijo())

    async def preload_historial_miembros(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal para cargar historial.", "error", "GoViral")
            return
        await log_discord(self.bot, "🔍 [GO-VIRAL] Cargando historial y usuarios antiguos...", "info", "GoViral")
        try:
            async for msg in canal.history(limit=None, oldest_first=True):
                if msg.author.bot: continue
                uid = str(msg.author.id)
                self.redis.set(f"go_viral:primera_pub:{uid}", "1")
                self.redis.set(f"go_viral:bienvenida:{uid}", "1")
            await log_discord(self.bot, "✅ [GO-VIRAL] Historial de usuarios antiguos sincronizado en Redis.", "success", "GoViral")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error cargando historial: {e}", "error", "GoViral")

    async def preload_apoyos_reacciones(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal para cargar reacciones.", "error", "GoViral")
            return
        await log_discord(self.bot, "🔄 [GO-VIRAL] Sincronizando reacciones 🔥 antiguas en Redis y limpiando reacciones no permitidas...", "info", "GoViral")
        try:
            mensajes = [msg async for msg in canal.history(limit=None, oldest_first=False)]
            for msg in mensajes:
                for reaction in msg.reactions:
                    if str(reaction.emoji) not in ["🔥", "👍"]:
                        async for user in reaction.users():
                            try:
                                await reaction.remove(user)
                            except Exception:
                                pass
                    elif str(reaction.emoji) == "🔥":
                        async for user in reaction.users():
                            if not user.bot:
                                self.redis.sadd(f"go_viral:apoyos:{msg.id}", str(user.id))
            await log_discord(self.bot, "✅ [GO-VIRAL] Apoyos sincronizados y reacciones limpiadas.", "success", "GoViral")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error sincronizando reacciones: {e}", "error", "GoViral")

    async def init_mensaje_fijo(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})", "error", "GoViral")
            return

        fecha = datetime.now().strftime("%Y-%m-%d")
        descripcion = DESCRIPCION_FIJO.format(fecha=fecha)
        hash_nuevo = calcular_hash_embed(TITULO_FIJO, descripcion, IMAGEN_URL)

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
                        await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo ya existe y está actualizado.", "success", "GoViral")
                        return
                    else:
                        embed_fijo = discord.Embed(
                            title=TITULO_FIJO,
                            description=descripcion,
                            color=discord.Color.blurple()
                        )
                        embed_fijo.set_image(url=IMAGEN_URL)
                        await mensaje.edit(embed=embed_fijo)
                        self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
                        await log_discord(self.bot, "🔄 [GO-VIRAL] Mensaje fijo actualizado.", "info", "GoViral")
                        return
            except Exception as e:
                await log_discord(self.bot, f"⚠️ [GO-VIRAL] No se pudo recuperar el mensaje guardado: {e}", "warning", "GoViral")

        embed_fijo = discord.Embed(
            title=TITULO_FIJO,
            description=descripcion,
            color=discord.Color.blurple()
        )
        embed_fijo.set_image(url=IMAGEN_URL)
        msg = await canal.send(embed=embed_fijo)
        await msg.pin()
        self.redis.set("go_viral:mensaje_fijo_id", str(msg.id))
        self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
        await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo publicado y registrado.", "success", "GoViral")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return

        user_id = str(message.author.id)
        key_bienvenida = f"go_viral:bienvenida:{user_id}"
        key_primera_publicacion = f"go_viral:primera_pub:{user_id}"

        url_limpia = limpiar_url_tweet(message.content)
        if not url_limpia:
            try:
                await message.delete()
            except Exception:
                pass
            embed = discord.Embed(
                title=TITULO_SOLO_URL_EDU,
                description=DESCRIPCION_SOLO_URL_EDU.format(usuario=message.author.mention),
                color=discord.Color.red()
            )
            try:
                await message.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            embed_dm = discord.Embed(
                title=TITULO_SOLO_URL_DM,
                description=DESCRIPCION_SOLO_URL_DM,
                color=discord.Color.red()
            )
            try:
                await message.author.send(embed=embed_dm)
            except Exception:
                pass
            await log_discord(self.bot, f"❌ [GO-VIRAL] {message.author} intentó publicar algo no permitido.", "warning", "GoViral")
            return

        if not self.redis.get(key_bienvenida):
            self.redis.set(key_bienvenida, "1")
            embed = discord.Embed(
                title=TITULO_BIENVENIDA,
                description=DESCRIPCION_BIENVENIDA,
                color=discord.Color.green()
            )
            embed.set_image(url=IMAGEN_URL)
            try:
                await message.reply(embed=embed, mention_author=True, delete_after=120)
                await log_discord(self.bot, f"✅ [GO-VIRAL] Bienvenida enviada a {message.author.display_name} ({user_id})", "success", "GoViral")
            except Exception as e:
                await log_discord(self.bot, f"❌ [GO-VIRAL] Error enviando bienvenida a {user_id}: {e}", "error", "GoViral")

        if url_limpia != message.content.strip():
            try:
                await message.delete()
            except Exception:
                pass
            try:
                await message.channel.send(f"{message.author.mention} {url_limpia}")
            except Exception:
                pass
            embed = discord.Embed(
                title=TITULO_URL_EDU,
                description=DESCRIPCION_URL_EDU,
                color=discord.Color.orange()
            )
            try:
                await message.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            embed_dm = discord.Embed(
                title=TITULO_URL_DM,
                description=DESCRIPCION_URL_DM.format(usuario=message.author.display_name),
                color=discord.Color.orange()
            )
            try:
                await message.author.send(embed=embed_dm)
            except Exception:
                pass
            await log_discord(self.bot, f"⚠️ [GO-VIRAL] Corrigiendo URL mal formateada de {message.author.display_name}", "warning", "GoViral")
            return

        if not self.redis.get(key_primera_publicacion):
            self.redis.set(key_primera_publicacion, "1")
            fecha_iso = datetime.now(timezone.utc).isoformat()
            self.redis.set(f"inactividad:{user_id}", fecha_iso)
            self.bot.loop.create_task(self.verificar_reaccion_like(message))
            return

        if not await self.verificar_intervalo_entre_publicaciones(message):
            return

        if not await self.verificar_apoyo_nueve_anteriores(message):
            return

        fecha_iso = datetime.now(timezone.utc).isoformat()
        self.redis.set(f"inactividad:{user_id}", fecha_iso)
        self.bot.loop.create_task(self.verificar_reaccion_like(message))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.channel.id != CANAL_OBJETIVO_ID or user.bot:
            return
        if str(reaction.emoji) not in ["🔥", "👍"]:
            try:
                await reaction.remove(user)
            except Exception:
                pass
            embed = discord.Embed(
                title=TITULO_SOLO_REACCION_EDU,
                description=DESCRIPCION_SOLO_REACCION_EDU.format(usuario=user.mention),
                color=discord.Color.red()
            )
            try:
                await reaction.message.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            embed_dm = discord.Embed(
                title=TITULO_SOLO_REACCION_DM,
                description=DESCRIPCION_SOLO_REACCION_DM,
                color=discord.Color.red()
            )
            try:
                await user.send(embed=embed_dm)
            except Exception:
                pass
            await log_discord(self.bot, f"❌ [GO-VIRAL] Reacción no permitida eliminada de {user.display_name}", "warning", "GoViral")
        if str(reaction.emoji) == "🔥" and not user.bot:
            self.redis.sadd(f"go_viral:apoyos:{reaction.message.id}", str(user.id))

    # Las siguientes funciones no cambian, puedes mantenerlas igual.

    async def verificar_intervalo_entre_publicaciones(self, message):
        canal = message.channel
        mensajes = [msg async for msg in canal.history(limit=50, oldest_first=False)]
        mensajes.reverse()
        idx_actual = None
        for i, msg in enumerate(mensajes):
            if msg.id == message.id:
                idx_actual = i
                break
        if idx_actual is None:
            return True

        idx_ultima = None
        for i in range(idx_actual - 1, -1, -1):
            if mensajes[i].author.id == message.author.id and not mensajes[i].author.bot:
                idx_ultima = i
                break

        if idx_ultima is None:
            return True

        publicaciones_otros = set()
        for i in range(idx_ultima + 1, idx_actual):
            msg = mensajes[i]
            if msg.author.id != message.author.id and not msg.author.bot:
                publicaciones_otros.add(msg.author.id)
            if len(publicaciones_otros) >= 2:
                break

        if len(publicaciones_otros) < 2:
            try:
                await message.delete()
            except Exception as e:
                pass
            embed = discord.Embed(
                title=TITULO_INTERVALO_EDU,
                description=DESCRIPCION_INTERVALO_EDU.format(usuario=message.author.mention),
                color=discord.Color.red()
            )
            try:
                await message.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            embed_dm = discord.Embed(
                title=TITULO_INTERVALO_DM,
                description=DESCRIPCION_INTERVALO_DM,
                color=discord.Color.red()
            )
            try:
                await message.author.send(embed=embed_dm)
            except Exception:
                pass
            await log_discord(self.bot, f"❌ [GO-VIRAL] Mensaje eliminado por intervalo insuficiente de {message.author.display_name}", "warning", "GoViral")
            return False
        return True

    async def verificar_apoyo_nueve_anteriores(self, message):
        canal = message.channel
        mensajes = [msg async for msg in canal.history(limit=50, oldest_first=False)]
        mensajes.reverse()
        idx = None
        for i, msg in enumerate(mensajes):
            if msg.id == message.id:
                idx = i
                break
        if idx is None:
            return True

        guild = canal.guild
        miembros_actuales = {str(m.id) for m in guild.members if not m.bot}
        posts_previos = []
        for msg in mensajes[:idx]:
            autor_id = str(msg.author.id)
            if autor_id in miembros_actuales:
                posts_previos.append(msg)

        revisar_posts = posts_previos if len(posts_previos) <= 9 else posts_previos[-9:]
        if len(revisar_posts) < 2:
            return True

        apoyo_faltante = []
        for post in revisar_posts:
            apoyaron = self.redis.smembers(f"go_viral:apoyos:{post.id}")
            if str(message.author.id) not in apoyaron:
                tiene_fuego = False
                for reaction in post.reactions:
                    if str(reaction.emoji) == "🔥":
                        async for user in reaction.users():
                            if user.id == message.author.id:
                                tiene_fuego = True
                                self.redis.sadd(f"go_viral:apoyos:{post.id}", str(user.id))
                                break
                    if tiene_fuego:
                        break
                if not tiene_fuego:
                    apoyo_faltante.append(post)

        if apoyo_faltante:
            try:
                await message.delete()
            except Exception as e:
                pass
            embed = discord.Embed(
                title=TITULO_APOYO_9_EDU,
                description=DESCRIPCION_APOYO_9_EDU.format(usuario=message.author.mention),
                color=discord.Color.red()
            )
            try:
                await message.channel.send(embed=embed, delete_after=15)
            except Exception as e:
                pass
            embed_dm = discord.Embed(
                title=TITULO_APOYO_9_DM,
                description=DESCRIPCION_APOYO_9_DM,
                color=discord.Color.red()
            )
            try:
                await message.author.send(embed=embed_dm)
            except Exception as e:
                pass
            await log_discord(self.bot, f"⛔ [GO-VIRAL] Eliminada publicación por no apoyar los 9 anteriores: {message.author.display_name}", "warning", "GoViral")
            return False
        return True

    async def verificar_reaccion_like(self, message):
        await asyncio.sleep(120)
        try:
            msg = await message.channel.fetch_message(message.id)
        except (discord.NotFound, discord.Forbidden):
            return

        autor = message.author
        tiene_like = False

        for reaction in msg.reactions:
            if str(reaction.emoji) == "👍":
                async for user in reaction.users():
                    if user.id == autor.id:
                        tiene_like = True
                        break

        if not tiene_like:
            try:
                await msg.delete()
            except Exception as e:
                pass
            embed = discord.Embed(
                title=TITULO_SIN_LIKE_EDU,
                description=DESCRIPCION_SIN_LIKE_EDU.format(usuario=autor.mention),
                color=discord.Color.red()
            )
            try:
                await msg.channel.send(embed=embed, delete_after=15)
            except Exception as e:
                pass
            embed_dm = discord.Embed(
                title=TITULO_SIN_LIKE_DM,
                description=DESCRIPCION_SIN_LIKE_DM,
                color=discord.Color.red()
            )
            try:
                await autor.send(embed=embed_dm)
            except Exception as e:
                pass
            await log_discord(self.bot, f"⛔ [GO-VIRAL] Eliminada publicación sin like de {autor.display_name}", "warning", "GoViral")
