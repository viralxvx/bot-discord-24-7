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
            print("❌ [GO-VIRAL] No se encontró el canal para cargar historial.")
            return
        print("🔍 [GO-VIRAL] Cargando historial y usuarios antiguos...")
        try:
            async for msg in canal.history(limit=None, oldest_first=True):
                if msg.author.bot: continue
                uid = str(msg.author.id)
                self.redis.set(f"go_viral:primera_pub:{uid}", "1")
                self.redis.set(f"go_viral:bienvenida:{uid}", "1")
            print("✅ [GO-VIRAL] Historial de usuarios antiguos sincronizado en Redis.")
        except Exception as e:
            print(f"❌ [GO-VIRAL] Error cargando historial: {e}")

    async def preload_apoyos_reacciones(self):
        """Escanea TODO el historial de mensajes y reacciones.
           - Guarda apoyos 🔥 en Redis (go_viral:apoyos:{post_id})
           - Elimina TODA reacción que NO sea 🔥 o 👍 de cualquier mensaje
        """
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            print("❌ [GO-VIRAL] No se encontró el canal para cargar apoyos.")
            return
        print("🔎 [GO-VIRAL] Cargando apoyos 🔥 y limpiando reacciones históricas...")
        try:
            async for msg in canal.history(limit=None, oldest_first=True):
                if msg.author.bot:
                    continue
                for reaction in msg.reactions:
                    # Si es 🔥, guardar todos los usuarios que apoyaron en Redis
                    if str(reaction.emoji) == "🔥":
                        async for usuario in reaction.users():
                            if usuario.bot:
                                continue
                            self.redis.sadd(f"go_viral:apoyos:{msg.id}", usuario.id)
                    # Si NO es 🔥 ni 👍, ELIMINAR la reacción de TODOS los usuarios
                    elif str(reaction.emoji) not in ["🔥", "👍"]:
                        async for usuario in reaction.users():
                            try:
                                await reaction.remove(usuario)
                                print(f"❌ [GO-VIRAL] Reacción prohibida {reaction.emoji} eliminada en mensaje {msg.id} de {usuario.display_name}")
                            except Exception as e:
                                print(f"⚠️ [GO-VIRAL] No se pudo eliminar reacción {reaction.emoji} en mensaje {msg.id}: {e}")
            print("✅ [GO-VIRAL] Apoyos 🔥 sincronizados y reacciones prohibidas eliminadas en TODO el canal.")
        except Exception as e:
            print(f"❌ [GO-VIRAL] Error cargando apoyos/reacciones: {e}")

    async def init_mensaje_fijo(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            print(f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})")
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
                        print("✅ [GO-VIRAL] Mensaje fijo ya existe y está actualizado.")
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
                        print("🔄 [GO-VIRAL] Mensaje fijo actualizado.")
                        return
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo recuperar el mensaje guardado: {e}")

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
        print("✅ [GO-VIRAL] Mensaje fijo publicado y registrado.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return

        user_id = str(message.author.id)
        key_bienvenida = f"go_viral:bienvenida:{user_id}"
        key_primera_publicacion = f"go_viral:primera_pub:{user_id}"

        # Solo permitir mensajes que sean URL válidas de x.com
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
            return

        # --- Bienvenida SOLO si no se ha enviado antes
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
                print(f"✅ [GO-VIRAL] Bienvenida enviada a {message.author.display_name} ({user_id})")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error enviando bienvenida a {user_id}: {e}")

        # --- Corrección automática de URLs mal formateadas ---
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
            return

        # --- Lógica para permitir PRIMERA publicación sin restricciones ---
        if not self.redis.get(key_primera_publicacion):
            self.redis.set(key_primera_publicacion, "1")
            fecha_iso = datetime.now(timezone.utc).isoformat()
            self.redis.set(f"inactividad:{user_id}", fecha_iso)
            self.bot.loop.create_task(self.verificar_reaccion_like(message))
            return

        # --- Control de intervalo entre publicaciones (mínimo 2 posts de otros después de ti) ---
        if not await self.verificar_intervalo_entre_publicaciones(message):
            return

        # --- Verificación de apoyo adaptativo (mínimo 2, máximo 9 previos) ---
        if not await self.verificar_apoyo_nueve_anteriores(message):
            return

        fecha_iso = datetime.now(timezone.utc).isoformat()
        self.redis.set(f"inactividad:{user_id}", fecha_iso)

        self.bot.loop.create_task(self.verificar_reaccion_like(message))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Permitir solo 👍 y 🔥 en el canal GO-VIRAL
        if reaction.message.channel.id != CANAL_OBJETIVO_ID or user.bot:
            return
        # Si es 🔥, registrar en Redis el apoyo
        if str(reaction.emoji) == "🔥":
            self.redis.sadd(f"go_viral:apoyos:{reaction.message.id}", user.id)
        # Eliminar cualquier reacción no autorizada
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

        # Buscar la última publicación válida de este usuario
        idx_ultima = None
        for i in range(idx_actual - 1, -1, -1):
            if mensajes[i].author.id == message.author.id and not mensajes[i].author.bot:
                idx_ultima = i
                break

        if idx_ultima is None:
            return True

        publicaciones_otros = []
        for i in range(idx_ultima + 1, idx_actual):
            msg = mensajes[i]
            if msg.author.id != message.author.id and not msg.author.bot:
                publicaciones_otros.append(msg)
            if len(publicaciones_otros) >= 2:
                break

        if len(publicaciones_otros) < 2:
            try:
                await message.delete()
                print(f"❌ [GO-VIRAL] Publicación de {message.author.display_name} eliminada por INTERVALO insuficiente (menos de 2 posts de otros después de él).")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje (intervalo): {e}")
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
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (intervalo) a {message.author.display_name}: {e}")
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

        # Filtra solo posts válidos de usuarios (no bots) antes de este mensaje
        posts_previos = []
        for msg in mensajes[:idx]:
            if not msg.author.bot:
                posts_previos.append(msg)

        # Adaptativo: Si hay menos de 9, exige todos; si hay más, solo los últimos 9
        if len(posts_previos) <= 9:
            revisar_posts = posts_previos
        else:
            revisar_posts = posts_previos[-9:]

        # Pero el mínimo siempre será 2 (solo verifica si hay al menos 2 previos)
        if len(revisar_posts) < 2:
            return True  # No exige apoyos si el canal está casi vacío

        apoyo_faltante = []
        for post in revisar_posts:
            apoyaron = self.redis.smembers(f"go_viral:apoyos:{post.id}")
            if str(message.author.id) not in apoyaron:
                apoyo_faltante.append(post)

        if apoyo_faltante:
            print(f"⛔ [{message.author.display_name}] le falta dar 🔥 a los siguientes mensajes:")
            for post in apoyo_faltante:
                print(f"  - ID: {post.id} | Autor: {post.author.display_name} | Contenido: {post.content[:50]}")
            try:
                await message.delete()
                print(f"❌ [GO-VIRAL] Publicación de {message.author.display_name} eliminada por NO apoyar a los previos requeridos.")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje (no apoyó): {e}")
            embed = discord.Embed(
                title=TITULO_APOYO_9_EDU,
                description=DESCRIPCION_APOYO_9_EDU.format(usuario=message.author.mention),
                color=discord.Color.red()
            )
            try:
                await message.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            embed_dm = discord.Embed(
                title=TITULO_APOYO_9_DM,
                description=DESCRIPCION_APOYO_9_DM,
                color=discord.Color.red()
            )
            try:
                await message.author.send(embed=embed_dm)
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (apoyo 9) a {message.author.display_name}: {e}")
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
                print(f"❌ [GO-VIRAL] Publicación eliminada por no validar con 👍: {autor.display_name}")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje sin like: {e}")
            embed = discord.Embed(
                title=TITULO_SIN_LIKE_EDU,
                description=DESCRIPCION_SIN_LIKE_EDU.format(usuario=autor.mention),
                color=discord.Color.red()
            )
            try:
                await msg.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            embed_dm = discord.Embed(
                title=TITULO_SIN_LIKE_DM,
                description=DESCRIPCION_SIN_LIKE_DM,
                color=discord.Color.red()
            )
            try:
                await autor.send(embed=embed_dm)
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (sin like) a {autor.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(GoViral(bot))
