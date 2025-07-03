import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, REDIS_URL
from mensajes.viral_texto import MENSAJE_FIJO, MENSAJE_BIENVENIDA_NUEVO, NOTIFICACION_URL_EDUCATIVA, NOTIFICACION_URL_DM
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

        # -------- Corrección automática de URL --------
        url_pattern = r'https://x\.com/[\w\d_]+/status/\d+'
        links = re.findall(url_pattern, message.content)
        if not links:
            # Busca si hay algún link mal formado de X/Twitter
            if "x.com" in message.content and "/status/" in message.content:
                url_base = re.search(url_pattern, message.content)
                if url_base:
                    url_limpio = url_base.group(0)
                    # Borra el mensaje del usuario
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"❌ [GO-VIRAL] Error borrando mensaje incorrecto: {e}")
                    # Re-publica simulando al usuario original (webhook)
                    webhooks = await message.channel.webhooks()
                    wh = None
                    for hook in webhooks:
                        if hook.user == self.bot.user:
                            wh = hook
                            break
                    if not wh:
                        wh = await message.channel.create_webhook(name="VXbotGO")
                    try:
                        await wh.send(
                            content=url_limpio,
                            username=message.author.display_name,
                            avatar_url=message.author.display_avatar.url if hasattr(message.author, 'display_avatar') else message.author.avatar_url
                        )
                        print(f"✅ [GO-VIRAL] URL corregida y publicada por {message.author.display_name}")
                        # Mensaje educativo en canal (15s)
                        try:
                            aviso = await message.channel.send(
                                NOTIFICACION_URL_EDUCATIVA,
                                reference=message,
                                delete_after=15
                            )
                        except Exception:
                            pass
                        # Mensaje DM educativo
                        try:
                            await message.author.send(
                                NOTIFICACION_URL_DM.format(usuario=message.author.display_name)
                            )
                        except Exception as e:
                            print(f"⚠️ [GO-VIRAL] No se pudo enviar DM educativo a {message.author.display_name}: {e}")
                    except Exception as e:
                        print(f"❌ [GO-VIRAL] Error en corrección automática: {e}")

def setup(bot):
    bot.add_cog(GoViral(bot))
