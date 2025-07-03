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
)
from datetime import datetime
import redis
import asyncio
import re

def limpiar_url_tweet(texto):
    """
    Extrae y limpia una URL válida de x.com/TUUSER/status/ID
    Retorna la url limpia si encuentra, sino None
    """
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

        # Busca mensaje fijo existente
        async for msg in canal.history(limit=20, oldest_first=True):
            if msg.author == self.bot.user and "¡Bienvenido a GO-VIRAL!" in msg.content:
                print("✅ [GO-VIRAL] Mensaje fijo ya existe.")
                return
        # Si no existe, publica y fija
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

        # --- Verificación de apoyo a los 9 anteriores ---
        if not await self.verificar_apoyo_nueve_anteriores(message):
            return  # Si falla, ya notificó y borró el mensaje

        # Inicia verificación de reacción 👍 del autor a su propio mensaje
        self.bot.loop.create_task(self.verificar_reaccion_like(message))

    async def verificar_apoyo_nueve_anteriores(self, message):
        """Valida si el usuario ha reaccionado 🔥 a los 9 posts anteriores antes de publicar."""
        canal = message.channel
        mensajes = [msg async for msg in canal.history(limit=50, oldest_first=False)]
        mensajes.reverse()  # De más antiguos a más nuevos

        # Busca la posición de este mensaje
        idx = None
        for i, msg in enumerate(mensajes):
            if msg.id == message.id:
                idx = i
                break
        if idx is None or idx < 9:
            # Primer post del usuario o no hay suficiente historia, deja pasar
            return True

        # Toma los 9 mensajes inmediatamente anteriores
        posts_previos = mensajes[idx-9:idx]
        apoyo_faltante = []
        for post in posts_previos:
            # Solo considera mensajes de miembros (no bots)
            if post.author.bot:
                continue
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
            # Elimina la publicación y notifica
            try:
                await message.delete()
                print(f"❌ [GO-VIRAL] Publicación de {message.author.display_name} eliminada por NO apoyar a los 9 anteriores.")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje (no apoyó a 9): {e}")

            # Mensaje educativo en canal
            try:
                await message.channel.send(
                    NOTIFICACION_APOYO_9_EDUCATIVA.format(usuario=message.author.mention),
                    delete_after=15
                )
            except Exception:
                pass
            # DM educativo
            try:
                await message.author.send(NOTIFICACION_APOYO_9_DM)
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (apoyo 9) a {message.author.display_name}: {e}")
            return False
        return True

    async def verificar_reaccion_like(self, message):
        """Espera 120 segundos y verifica si el autor reaccionó con 👍 a su propio mensaje"""
        await asyncio.sleep(120)
        try:
            msg = await message.channel.fetch_message(message.id)
        except (discord.NotFound, discord.Forbidden):
            # El mensaje ya no existe
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
            # Elimina mensaje, notifica en canal y por DM
            try:
                await msg.delete()
                print(f"❌ [GO-VIRAL] Publicación eliminada por no validar con 👍: {autor.display_name}")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje sin like: {e}")
            # Mensaje educativo en canal (15s)
            try:
                await msg.channel.send(
                    NOTIFICACION_SIN_LIKE_EDUCATIVA.format(usuario=autor.mention),
                    delete_after=15
                )
            except Exception:
                pass
            # DM educativo
            try:
                await autor.send(NOTIFICACION_SIN_LIKE_DM)
            except Exception as e:
                print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (sin like) a {autor.display_name}: {e}")

def setup(bot):
    bot.add_cog(GoViral(bot))
