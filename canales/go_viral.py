import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, REDIS_URL
from mensajes.viral_texto import (
    MENSAJE_FIJO,
    MENSAJE_BIENVENIDA_NUEVO,
    NOTIFICACION_URL_EDUCATIVA,
    NOTIFICACION_URL_DM,
    NOTIFICACION_SIN_LIKE_EDUCATIVA,
    NOTIFICACION_SIN_LIKE_DM
)
from datetime import datetime
import redis
import asyncio
import re

def limpiar_url_tweet(texto):
    """
    Extrae y devuelve la URL limpia de X/Twitter si está presente.
    """
    # Acepta variantes con parámetros y los limpia
    patron = re.compile(r'https?://x\.com/[^/\s]+/status/(\d+)')
    coincidencias = patron.findall(texto)
    if coincidencias:
        # Usa solo el primer match, limpia el texto
        return f"https://x.com/{re.search(r'x\.com/([^/\s]+)/status', texto).group(1)}/status/{coincidencias[0]}"
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

        # --- Fase 7: Corrección automática de URLs ---
        # Detectar y corregir URL si está mal
        url_limpia = limpiar_url_tweet(message.content)
        if url_limpia:
            # ¿El mensaje ya era limpio? Si sí, nada.
            if url_limpia == message.content.strip():
                pass  # Ya está perfecto
            else:
                try:
                    await message.delete()
                    print(f"🧹 [GO-VIRAL] Mensaje con URL mal formateada eliminado ({message.author.display_name})")
                except Exception as e:
                    print(f"❌ [GO-VIRAL] Error al borrar mensaje con URL mal: {e}")

                # Re-publica como si fuera el usuario (mencionándolo)
                try:
                    nuevo_msg = await message.channel.send(
                        f"{message.author.mention} {url_limpia}"
                    )
                    print(f"✅ [GO-VIRAL] URL corregida y republicada para {message.author.display_name}")
                except Exception as e:
                    print(f"❌ [GO-VIRAL] Error al republicar URL limpia: {e}")

                # Mensaje educativo en canal (15s)
                try:
                    aviso = await message.channel.send(
                        NOTIFICACION_URL_EDUCATIVA,
                        delete_after=15
                    )
                except Exception:
                    pass
                # DM educativo
                try:
                    await message.author.send(
                        NOTIFICACION_URL_DM.format(usuario=message.author.display_name)
                    )
                except Exception as e:
                    print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (URL): {e}")
                return  # ¡No sigas! Ya procesado.

        # Inicia verificación de reacción 👍 del autor a su propio mensaje
        self.bot.loop.create_task(self.verificar_reaccion_like(message))

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
