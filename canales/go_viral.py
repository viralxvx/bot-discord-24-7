import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, REDIS_URL
from mensajes.viral_texto import (
    MENSAJE_FIJO,
    MENSAJE_BIENVENIDA_NUEVO,
    NOTIFICACION_URL_EDUCATIVA,
    NOTIFICACION_URL_DM
)
from datetime import datetime
import redis
import re

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

        # Envío de bienvenida SOLO si no se ha enviado antes
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

        # ---- FASE 5: Corrección automática de URL ----
        url_pattern = r"https://x\.com/[\w\d_]+/status/\d+"
        urls_encontradas = re.findall(r"https://[^\s]+", message.content)
        if urls_encontradas:
            url = urls_encontradas[0]
            # Si el enlace no cumple el patrón limpio, corregirlo
            if not re.match(url_pattern, url):
                url_limpio = re.search(url_pattern, url)
                if url_limpio:
                    url_limpio = url_limpio.group(0)
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"❌ [GO-VIRAL] Error borrando mensaje original: {e}")
                    try:
                        await message.channel.send(
                            f"{message.author.mention} {url_limpio}"
                        )
                        print(f"🔁 [GO-VIRAL] URL corregida para {message.author.display_name}: {url_limpio}")
                    except Exception as e:
                        print(f"❌ [GO-VIRAL] Error re-publicando URL corregida: {e}")
                    # Notificación educativa (canal, 15s)
                    try:
                        await message.channel.send(
                            NOTIFICACION_URL_EDUCATIVA,
                            delete_after=15
                        )
                    except Exception:
                        pass
                    # Notificación por DM
                    try:
                        await message.author.send(NOTIFICACION_URL_DM.format(usuario=message.author.mention))
                    except Exception as e:
                        print(f"⚠️ [GO-VIRAL] No se pudo enviar DM a {message.author.display_name}: {e}")

def setup(bot):
    bot.add_cog(GoViral(bot))
