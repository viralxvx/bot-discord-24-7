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
import aiohttp
import asyncio
import re

# Regex de URL correcta de x.com
URL_X_LIMPIO = re.compile(r"^https://x\.com/[\w\d_]+/status/\d+$")

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

        # ========== CORRECCIÓN AUTOMÁTICA DE URL ==========
        urls = re.findall(r"https://x\.com/[\w\d_]+/status/\d+(?:\?[^ ]*)?", message.content)
        if urls:
            url = urls[0]
            if not URL_X_LIMPIO.match(url):
                # Corrige la URL al formato limpio
                url_corr = re.match(r"(https://x\.com/[\w\d_]+/status/\d+)", url)
                if url_corr:
                    url_limpio = url_corr.group(1)
                    # Borra mensaje original
                    try:
                        await message.delete()
                        print(f"⚠️ [GO-VIRAL] Enlace corregido automáticamente para {message.author.display_name}: {url_limpio}")
                    except Exception as e:
                        print(f"❌ [GO-VIRAL] Error borrando mensaje mal formateado: {e}")
                    # Publica como el usuario con webhook
                    await self.publicar_como_usuario(message, url_limpio)
                    # Mensaje educativo en canal
                    try:
                        aviso = await message.channel.send(
                            NOTIFICACION_URL_EDUCATIVA,
                            delete_after=15
                        )
                    except Exception:
                        pass
                    # DM al usuario
                    try:
                        await message.author.send(NOTIFICACION_URL_DM.format(usuario=message.author.mention))
                    except Exception as e:
                        print(f"⚠️ [GO-VIRAL] No se pudo enviar DM (URL) a {message.author.display_name}: {e}")
                    # Log/registro en Redis
                    self.redis.set(f"go_viral:url_corregida:{user_id}:{message.id}", datetime.utcnow().isoformat())
                    return  # No sigue el flujo, ya lo republicó

        # ========== BIENVENIDA SOLO UNA VEZ ==========
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

        # ========== VERIFICACIÓN DE 👍 EN 2 MINUTOS ==========
        self.bot.loop.create_task(self.verificar_reaccion_like(message))

    async def publicar_como_usuario(self, original_msg, url_limpia):
        """Re-publica el mensaje como si fuera el usuario usando un webhook (nombre y avatar igual al autor)"""
        canal = original_msg.channel
        webhooks = await canal.webhooks()
        wh = None
        # Reusa un webhook existente si es del bot, si no crea uno
        for w in webhooks:
            if w.user == self.bot.user:
                wh = w
                break
        if wh is None:
            wh = await canal.create_webhook(name="VXbotAutoPub")

        async with aiohttp.ClientSession() as session:
            await wh.send(
                content=url_limpia,
                username=original_msg.author.display_name,
                avatar_url=original_msg.author.display_avatar.url,
                allowed_mentions=discord.AllowedMentions(users=True),
                wait=True,
                session=session
            )
        print(f"✅ [GO-VIRAL] URL republicada como usuario: {original_msg.author.display_name}")

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
