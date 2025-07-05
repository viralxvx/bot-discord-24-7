import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, REDIS_URL
from mensajes.viral_texto import (
    TITULO_FIJO, DESCRIPCION_FIJO, IMAGEN_URL,
    TITULO_BIENVENIDA, DESCRIPCION_BIENVENIDA,
    TITULO_URL_EDU, DESCRIPCION_URL_EDU,
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

# Función para manejar el rate limiting y enviar mensajes con reintentos
async def enviar_mensaje_con_reintento(canal, embed):
    for intento in range(5):  # Intentar hasta 5 veces
        try:
            await canal.send(embed=embed)  # Intentamos enviar el mensaje
            return  # Si el mensaje se envía correctamente, salimos
        except discord.errors.HTTPException as e:
            if e.code == 429:  # Si el error es rate limiting (429)
                wait_time = 2 ** intento  # Exponential backoff (espera más tiempo con cada intento)
                await log_discord(self.bot, f"Rate limiting detectado. Esperando {wait_time} segundos...")
                await asyncio.sleep(wait_time)  # Esperamos antes de reintentar
            else:
                # Si es otro error, lo registramos y salimos
                await log_discord(self.bot, f"Error inesperado al enviar mensaje: {e}")
                break

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
        self.tareas_ejecutadas = set()  # Mantener un registro de las tareas realizadas
        bot.loop.create_task(self.preload_historial_miembros())
        bot.loop.create_task(self.preload_apoyos_reacciones())
        bot.loop.create_task(self.init_mensaje_fijo())

    async def preload_historial_miembros(self):
        if 'preload_historial_miembros' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('preload_historial_miembros')  # Marca esta tarea como ejecutada

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
        if 'preload_apoyos_reacciones' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('preload_apoyos_reacciones')  # Marca esta tarea como ejecutada

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
        if 'init_mensaje_fijo' in self.tareas_ejecutadas:
            return
        self.tareas_ejecutadas.add('init_mensaje_fijo')  # Marca esta tarea como ejecutada

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
        msg = await enviar_mensaje_con_reintento(canal, embed_fijo)  # Reemplazar por la nueva función
        await msg.pin()
        self.redis.set("go_viral:mensaje_fijo_id", str(msg.id))
        self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
        await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo publicado y registrado.", "success", "GoViral")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return

        user_id = str(message.author.id)

        # Verificar si el usuario tiene override
        if self.redis.get(f"go_viral:override:{message.author.id}") == "1":
            await log_discord(self.bot, f"✅ [GO-VIRAL] {message.author} tiene override y su mensaje fue permitido.", "info", "GoViral")
            return
            
        # Resto de las validaciones del mensaje (URL mal formateada, etc.)

    # Asegúrate de agregar la función setup
async def setup(bot):
    await bot.add_cog(GoViral(bot))
