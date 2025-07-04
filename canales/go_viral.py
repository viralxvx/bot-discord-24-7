import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, REDIS_URL
from mensajes.viral_texto import (
    MENSAJE_FIJO,
    MENSAJE_BIENVENIDA_NUEVO,
    NOTIFICACION_URL_EDUCATIVA,
    NOTIFICACION_URL_DM,
    NOTIFICACION_SIN_LIKE_EDUCATIVA,
    NOTIFICACION_SIN_LIKE_DM,
    NOTIFICACION_APOYO_9_EDUCATIVA,
    NOTIFICACION_APOYO_9_DM,
    NOTIFICACION_INTERVALO_EDUCATIVA,
    NOTIFICACION_INTERVALO_DM
)
from datetime import datetime, timedelta, timezone
import redis
import asyncio
import re

def limpiar_url_tweet(texto):
    match = re.search(r"https?://x\.com/\w+/status/(\d+)", texto)
    if match:
        usuario = re.search(r"https?://x\.com/([^/]+)/status", texto)
        if usuario:
            user = usuario.group(1)
            status_id = match.group(1)
            return f"https://x.com/{user}/status/{status_id}"
    return None

class GoViral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.init_mensaje_fijo())

    async def init_mensaje_fijo(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            print(f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})")
            return
        async for msg in canal.history(limit=20, oldest_first=True):
            if msg.author == self.bot.user and "¡Bienvenido a GO-VIRAL!" in msg.content:
                print("✅ [GO-VIRAL] Mensaje fijo ya existe.")
                return
        fecha = datetime.now().strftime("%Y-%m-%d")
        msg = await canal.send(MENSAJE_FIJO.format(fecha=fecha))
        try:
            await msg.pin()
            print("✅ [GO-VIRAL] Mensaje fijo publicado y fijado.")
        except Exception as e:
            print(f"⚠️ [GO-VIRAL] Error fijando mensaje: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return

        user_id = str(message.author.id)
        key_bienvenida = f"go_viral:bienvenida:{user_id}"

        # Bienvenida SOLO si no se ha enviado antes
        if not self.redis.get(key_bienvenida):
            self.redis.set(key_bienvenida, "1")
            try:
                await message.reply(
                    MENSAJE_BIENVENIDA_NUEVO,
                    mention_author=True,
                    delete_after=120
                )
                print(f"✅ [GO-VIRAL] Bienvenida enviada a {message.author.display_name} ({user_id})")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error enviando bienvenida a {user_id}: {e}")

        # --- Corrección automática de URLs mal formateadas ---
        url_limpia = limpiar_url_tweet(message.content)
        if url_limpia:
            if url_limpia == message.content.strip():
                pass  # ya está limpia, sigue
            else:
                try:
                    await message.delete()
                except: pass
                try:
                    await message.channel.send(f"{message.author.mention} {url_limpia}")
                except: pass
                try:
                    await message.channel.send(NOTIFICACION_URL_EDUCATIVA, delete_after=15)
                except: pass
                try:
                    await message.author.send(NOTIFICACION_URL_DM.format(usuario=message.author.display_name))
                except: pass
                return

        # --- Control de intervalo entre publicaciones ---
        if not await self.verificar_intervalo_entre_publicaciones(message):
            return  # Si falla, ya notificó y borró el mensaje

        # --- Verificación de apoyo a los anteriores (hasta 9, pero puede ser menos) ---
        if not await self.verificar_apoyo_anteriores(message):
            return  # Si falla, ya notificó y borró el mensaje

        # Inicia verificación de reacción 👍 del autor a su propio mensaje
        self.bot.loop.create_task(self.verificar_reaccion_like(message))

    async def verificar_intervalo_entre_publicaciones(self, message):
        """
        Permite publicar si hay al menos 2 publicaciones válidas de otros miembros
        desde la última publicación de este usuario
        O si han pasado 24 horas desde su última publicación
        """
        canal = message.channel
        mensajes = [msg async for msg in canal.history(limit=50, oldest_first=False)]
        mensajes.reverse()  # Más antiguo a más nuevo

        # Busca la última publicación de este usuario antes de este mensaje
        idx_actual = None
        for i, msg in enumerate(mensajes):
            if msg.id == message.id:
                idx_actual = i
                break
        if idx_actual is None:
            return True  # Mensaje fantasma, dejar pasar

        idx_ultima = None
        for i in range(idx_actual - 1, -1, -1):
            if mensajes[i].author.id == message.author.id and not mensajes[i].author.bot:
                idx_ultima = i
                break

        if idx_ultima is None:
            return True  # Es su primer post

        # Si han pasado más de 24h desde su última publicación, permitir
        ultima_fecha = mensajes[idx_ultima].created_at.replace(tzinfo=timezone.utc)
        ahora = datetime.now(timezone.utc)
        if (ahora - ultima_fecha).total_seconds() >= 24 * 3600:
            return True

        # Contar cuántas publicaciones válidas (de otros usuarios) hay entre la última y la actual
        publicaciones_otros = set()
        for i in range(idx_ultima + 1, idx_actual):
            msg = mensajes[i]
            if msg.author.id != message.author.id and not msg.author.bot:
                publicaciones_otros.add(msg.author.id)
            if len(publicaciones_otros) >= 2:
                break

        if len(publicaciones_otros) < 2:
            # Elimina la publicación y notifica
            try:
                await message.delete()
                print(f"❌ [GO-VIRAL] Publicación de {message.author.display_name} eliminada por INTERVALO insuficiente.")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje (intervalo): {e}")
            try:
                await message.channel.send(
                    NOTIFICACION_INTERVALO_EDUCATIVA.format(usuario=message.author.mention),
                    delete_after=15
                )
            except Exception:
                pass
            try:
                await message.author.send(NOTIFICACION_INTERVALO_DM)
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (intervalo) a {message.author.display_name}: {e}")
            return False
        return True

    async def verificar_apoyo_anteriores(self, message):
        """
        Verifica que el usuario haya apoyado con 🔥 a TODAS las publicaciones previas (hasta 9, o menos si hay menos).
        Solo revisa los posts desde la última publicación suya.
        """
        canal = message.channel
        mensajes = [msg async for msg in canal.history(limit=50, oldest_first=False)]
        mensajes.reverse()  # De más antiguos a más nuevos

        idx = None
        for i, msg in enumerate(mensajes):
            if msg.id == message.id:
                idx = i
                break
        if idx is None:
            return True  # Mensaje fantasma o error

        # Busca la última publicación de este usuario antes de este mensaje
        idx_ultima = None
        for i in range(idx - 1, -1, -1):
            if mensajes[i].author.id == message.author.id and not mensajes[i].author.bot:
                idx_ultima = i
                break

        # Si nunca ha publicado antes, no se exige apoyo previo
        if idx_ultima is None:
            return True

        # Solo contar publicaciones de otros después de su última publicación (máximo 9)
        posts_previos = []
        for i in range(idx_ultima + 1, idx):
            post = mensajes[i]
            if not post.author.bot and post.author.id != message.author.id:
                posts_previos.append(post)
            if len(posts_previos) >= 9:
                break

        # Si hay menos de 9, solo exigir los que haya
        apoyo_faltante = []
        for post in posts_previos:
            tiene_fuego = False
            for reaction in post.reactions:
                if str(reaction.emoji) == "🔥":
                    async for user in reaction.users():
                        if user.id == message.author.id:
                            tiene_fuego = True
                            break
                if tiene_fuego:
                    break
            if not tiene_fuego:
                apoyo_faltante.append(post)

        if apoyo_faltante:
            try:
                await message.delete()
                print(f"❌ [GO-VIRAL] Publicación de {message.author.display_name} eliminada por NO apoyar a los {len(posts_previos)} anteriores.")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje (no apoyó): {e}")
            try:
                await message.channel.send(
                    NOTIFICACION_APOYO_9_EDUCATIVA.format(usuario=message.author.mention),
                    delete_after=15
                )
            except Exception:
                pass
            try:
                await message.author.send(NOTIFICACION_APOYO_9_DM)
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (apoyo) a {message.author.display_name}: {e}")
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
            try:
                await msg.channel.send(
                    NOTIFICACION_SIN_LIKE_EDUCATIVA.format(usuario=autor.mention),
                    delete_after=15
                )
            except Exception:
                pass
            try:
                await autor.send(NOTIFICACION_SIN_LIKE_DM)
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (sin like) a {autor.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(GoViral(bot))
