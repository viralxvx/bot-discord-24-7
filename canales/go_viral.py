# go viral
import discord
from discord.ext import commands
from config import (
    CANAL_OBJETIVO_ID, EMOJIS_PERMITIDOS, REDIS_URL
)
from mensajes.viral_texto import (
    TITULO_FIJO, DESCRIPCION_FIJO, IMAGEN_URL,
    TITULO_BIENVENIDA, DESCRIPCION_BIENVENIDA,
    TITULO_APOYO_9_EDU, DESCRIPCION_APOYO_9_EDU,
    TITULO_APOYO_9_DM, DESCRIPCION_APOYO_9_DM,
    TITULO_INTERVALO_EDU, DESCRIPCION_INTERVALO_EDU,
    TITULO_INTERVALO_DM, DESCRIPCION_INTERVALO_DM,
    TITULO_SIN_LIKE_EDU, DESCRIPCION_SIN_LIKE_EDU,
    TITULO_SIN_LIKE_DM, DESCRIPCION_SIN_LIKE_DM,
    TITULO_SOLO_URL_EDU, DESCRIPCION_SOLO_URL_EDU,
    TITULO_SOLO_URL_DM, DESCRIPCION_SOLO_URL_DM,
    TITULO_SOLO_REACCION_EDU, DESCRIPCION_SOLO_REACCION_EDU,
    TITULO_SOLO_REACCION_DM, DESCRIPCION_SOLO_REACCION_DM,
)
from utils.logger import log_discord
from canales.faltas import registrar_falta
from datetime import datetime, timezone
import asyncio
import re
import redis

# ----- CONFIGURACIÓN REGLAS -----
MAX_APOYOS = 9         # Posts a apoyar antes de publicar (0 para desactivar)
MIN_TURNOS = 2         # Turnos de espera mínimo antes de publicar de nuevo
INTERVALO_HORAS = 24   # Horas máximas de espera para volver a publicar
BIENVENIDA_TIEMPO = 120  # Segundos que dura el mensaje de bienvenida primer post
NOTIF_TIEMPO = 15      # Segundos que duran los mensajes educativos de error en canal

class GoViral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.preload_apoyos_reacciones())
        bot.loop.create_task(self.limpiar_reacciones_no_permitidas())
        bot.loop.create_task(self.init_mensaje_fijo())
        bot.loop.create_task(self.reconstruir_ultimo_apoyo_por_usuario())  # NUEVO: memoria perfecta

    async def preload_apoyos_reacciones(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal para sincronizar apoyos.", "error", scope="go_viral")
            return
        await log_discord(self.bot, "🔄 [GO-VIRAL] Sincronizando apoyos y validaciones de últimos 100 mensajes...", "info", scope="go_viral")
        try:
            pipe = self.redis.pipeline()
            async for msg in canal.history(limit=100, oldest_first=True):
                apoyos_key = f"go_viral:apoyos:{msg.id}"
                validaciones_key = f"go_viral:validaciones:{msg.id}"
                pipe.delete(apoyos_key)
                pipe.delete(validaciones_key)
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "🔥":
                        async for user in reaction.users():
                            if not user.bot:
                                pipe.sadd(apoyos_key, str(user.id))
                    if str(reaction.emoji) == "👍":
                        async for user in reaction.users():
                            if not user.bot:
                                pipe.sadd(validaciones_key, str(user.id))
            pipe.execute()
            await log_discord(self.bot, "✅ [GO-VIRAL] Apoyos y validaciones sincronizados.", "success", scope="go_viral")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error sincronizando apoyos: {e}", "error", scope="go_viral")

    async def reconstruir_ultimo_apoyo_por_usuario(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal para reconstruir último apoyo.", "error", scope="go_viral")
            return
        mapping = {}
        async for msg in canal.history(limit=100, oldest_first=True):
            if msg.author.bot:
                continue
            uid = str(msg.author.id)
            mapping[uid] = msg.id  # Siempre queda el último mensaje válido
        # Guardar en redis
        for uid, msgid in mapping.items():
            self.redis.set(f"go_viral:ultimo_apoyo_completo:{uid}", str(msgid))
        await log_discord(self.bot, f"✅ [GO-VIRAL] Memoria reconstruida para {len(mapping)} usuarios.", "success", scope="go_viral")

    async def limpiar_reacciones_no_permitidas(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal para limpiar reacciones.", "error", scope="go_viral")
            return
        await log_discord(self.bot, "🔄 [GO-VIRAL] Limpiando reacciones no permitidas en últimos 100 mensajes...", "info", scope="go_viral")
        try:
            async for msg in canal.history(limit=100, oldest_first=False):
                # REGLA NUEVA: Si el post es propio, SOLO se permite 👍
                for reaction in msg.reactions:
                    async for user in reaction.users():
                        if not user.bot:
                            # Si el mensaje es del usuario y la reacción NO es 👍, la borra
                            if msg.author.id == user.id and str(reaction.emoji) != "👍":
                                await reaction.remove(user)
                                await self.notificar_reaccion_no_permitida(msg.channel, user, msg)
                            # Si la reacción no es permitida por nadie, la borra
                            elif str(reaction.emoji) not in EMOJIS_PERMITIDOS:
                                await reaction.remove(user)
                                await self.notificar_reaccion_no_permitida(msg.channel, user, msg)
            await log_discord(self.bot, "✅ [GO-VIRAL] Reacciones no permitidas eliminadas.", "success", scope="go_viral")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error limpiando reacciones: {e}", "error", scope="go_viral")

    async def init_mensaje_fijo(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})", "error", scope="go_viral")
            return
        fecha = datetime.now().strftime("%Y-%m-%d")
        descripcion = DESCRIPCION_FIJO.format(fecha=fecha)
        msg_id_guardado = self.redis.get("go_viral:mensaje_fijo_id")
        hash_nuevo = f"{TITULO_FIJO}|{descripcion}|{IMAGEN_URL}"
        hash_guardado = self.redis.get("go_viral:mensaje_fijo_hash")
        if msg_id_guardado and hash_nuevo == hash_guardado:
            return
        embed_fijo = discord.Embed(
            title=TITULO_FIJO,
            description=descripcion,
            color=discord.Color.blurple()
        )
        if IMAGEN_URL:
            embed_fijo.set_image(url=IMAGEN_URL)
        if msg_id_guardado:
            try:
                mensaje = await canal.fetch_message(int(msg_id_guardado))
                await mensaje.edit(embed=embed_fijo)
                self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
                await log_discord(self.bot, "🔄 [GO-VIRAL] Mensaje fijo editado.", "info", scope="go_viral")
                return
            except:
                pass
        msg = await canal.send(embed=embed_fijo)
        await msg.pin()
        self.redis.set("go_viral:mensaje_fijo_id", str(msg.id))
        self.redis.set("go_viral:mensaje_fijo_hash", hash_nuevo)
        await log_discord(self.bot, "✅ [GO-VIRAL] Mensaje fijo publicado.", "success", scope="go_viral")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id != CANAL_OBJETIVO_ID:
            return
        emoji = str(payload.emoji)
        user = await self.bot.fetch_user(payload.user_id)
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        mensaje = await canal.fetch_message(payload.message_id)
        if user.bot:
            return
        # PROPIO: solo 👍 permitido
        if mensaje.author.id == user.id and emoji != "👍":
            await mensaje.clear_reaction(emoji)
            await self.notificar_reaccion_no_permitida(canal, user, mensaje)
            return
        # General: solo 🔥 y 👍 permitidos
        if emoji not in EMOJIS_PERMITIDOS:
            await mensaje.clear_reaction(emoji)
            await self.notificar_reaccion_no_permitida(canal, user, mensaje)
            await log_discord(self.bot, f"🚫 [GO-VIRAL] Reacción no permitida {emoji} eliminada a {user}", "warning", scope="go_viral")
            return
        if emoji == "🔥":
            self.redis.sadd(f"go_viral:apoyos:{mensaje.id}", str(user.id))
        if emoji == "👍":
            self.redis.sadd(f"go_viral:validaciones:{mensaje.id}", str(user.id))

    async def notificar_reaccion_no_permitida(self, canal, user, mensaje):
        embed = discord.Embed(
            title=TITULO_SOLO_REACCION_EDU,
            description=DESCRIPCION_SOLO_REACCION_EDU.format(usuario=user.mention),
            color=discord.Color.orange()
        )
        await canal.send(content=user.mention, embed=embed, delete_after=NOTIF_TIEMPO)
        try:
            await user.send(embed=discord.Embed(
                title=TITULO_SOLO_REACCION_DM,
                description=DESCRIPCION_SOLO_REACCION_DM,
                color=discord.Color.orange()
            ))
        except:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return

        user_id = str(message.author.id)

        # --- 0. OVERRIDE: Permite 1 publicación libre ---
        if self.redis.get(f"go_viral:override:{user_id}") == "1":
            self.redis.delete(f"go_viral:override:{user_id}")
            await self.enviar_bienvenida(message)
            self.redis.set(f"go_viral:ultimo_apoyo_completo:{user_id}", str(message.id))
            await log_discord(self.bot, f"✅ [GO-VIRAL] OVERRIDE aplicado a {message.author}. Publica libremente.", "info", scope="go_viral")
            return

        # --- 1. Validar formato de publicación (sólo URLs limpias, CORRIGE SI ESTÁ MAL) ---
        url = limpiar_url_tweet(message.content)
        if not url:
            await message.delete()
            # Trata de corregir automáticamente
            url_corregida = extraer_url_tweet(message.content)
            if url_corregida:
                # Re-publica el mensaje como si fuera el usuario
                canal = message.channel
                new_msg = await canal.send(f"{message.author.mention} {url_corregida}")
                # Copia todas las menciones originales si las hay (opcional)
                await self.notif_full(new_msg, TITULO_SOLO_URL_EDU, DESCRIPCION_SOLO_URL_EDU.format(usuario=message.author.mention), TITULO_SOLO_URL_DM, DESCRIPCION_SOLO_URL_DM, user_id, "Formato incorrecto de publicación (corregido)")
                await log_discord(self.bot, f"🔧 [GO-VIRAL] Corrigió automáticamente el enlace de {message.author}", "info", scope="go_viral")
            else:
                await self.notif_full(message, TITULO_SOLO_URL_EDU, DESCRIPCION_SOLO_URL_EDU.format(usuario=message.author.mention), TITULO_SOLO_URL_DM, DESCRIPCION_SOLO_URL_DM, user_id, "Formato incorrecto de publicación")
            return

        # --- 2. Primer post: Permitir publicar y enviar bienvenida educativa (1 vez) ---
        primer_post_key = f"go_viral:primer_post:{user_id}"
        if not self.redis.get(primer_post_key):
            self.redis.set(primer_post_key, "1")
            await self.enviar_bienvenida(message)
            self.redis.set(f"go_viral:ultimo_apoyo_completo:{user_id}", str(message.id))
            await log_discord(self.bot, f"🎉 [GO-VIRAL] Primer post de {message.author}. Publicación permitida.", "info", scope="go_viral")
            return

        # --- 3. Chequear apoyo a anteriores (🔥) ---
        last_apoyo_key = f"go_viral:ultimo_apoyo_completo:{user_id}"
        last_apoyo_id = self.redis.get(last_apoyo_key)
        posts_previos = await self.obtener_publicaciones_previas(message, last_apoyo_id)
        posts_a_apoyar = posts_previos[-MAX_APOYOS:] if MAX_APOYOS > 0 else []
        apoyos_ok = True
        for post in posts_a_apoyar:
            if not self.usuario_ya_apoyo(user_id, post):
                apoyos_ok = False
                break
        if not apoyos_ok:
            await message.delete()
            await self.notif_full(message, TITULO_APOYO_9_EDU, DESCRIPCION_APOYO_9_EDU.format(usuario=message.author.mention),
                                  TITULO_APOYO_9_DM, DESCRIPCION_APOYO_9_DM, user_id, "No apoyar publicaciones anteriores")
            return

        # --- 4. Chequear intervalos (turnos y horas) ---
        ultima_pub, turnos_entre = await self.ultima_publicacion_y_turnos(message)
        ahora = datetime.now(timezone.utc)
        horas_desde_ultima = (ahora - ultima_pub).total_seconds() / 3600 if ultima_pub else None

        if (turnos_entre < MIN_TURNOS) and (horas_desde_ultima is None or horas_desde_ultima < INTERVALO_HORAS):
            await message.delete()
            await self.notif_full(message, TITULO_INTERVALO_EDU, DESCRIPCION_INTERVALO_EDU.format(usuario=message.author.mention),
                                  TITULO_INTERVALO_DM, DESCRIPCION_INTERVALO_DM, user_id, "No respetar intervalo de publicaciones")
            return

        # --- 5. Esperar validación con 👍 (2min) ---
        await asyncio.sleep(120)
        try:
            mensaje = await message.channel.fetch_message(message.id)
        except:
            # Ya fue eliminado
            return
        validado = False
        for reaction in mensaje.reactions:
            if str(reaction.emoji) == "👍":
                async for user in reaction.users():
                    if user.id == message.author.id:
                        validado = True
                        self.redis.sadd(f"go_viral:validaciones:{mensaje.id}", str(user.id))
                        break
        if not validado:
            await mensaje.delete()
            await self.notif_full(mensaje, TITULO_SIN_LIKE_EDU, DESCRIPCION_SIN_LIKE_EDU.format(usuario=message.author.mention),
                                  TITULO_SIN_LIKE_DM, DESCRIPCION_SIN_LIKE_DM, user_id, "No validar publicación con 👍 en 2 minutos")
            return

        # --- 6. Guardar apoyos y validaciones (para futuro) ---
        self.redis.delete(f"go_viral:apoyos:{message.id}")
        self.redis.delete(f"go_viral:validaciones:{message.id}")
        for reaction in mensaje.reactions:
            if str(reaction.emoji) == "🔥":
                async for user in reaction.users():
                    if not user.bot:
                        self.redis.sadd(f"go_viral:apoyos:{message.id}", str(user.id))
            if str(reaction.emoji) == "👍":
                async for user in reaction.users():
                    if not user.bot:
                        self.redis.sadd(f"go_viral:validaciones:{message.id}", str(user.id))

        self.redis.set(f"go_viral:ultimo_apoyo_completo:{user_id}", str(message.id))
        await log_discord(self.bot, f"✅ [GO-VIRAL] Mensaje válido de {message.author}: {url}", "info", scope="go_viral")
        await self.bot.process_commands(message)

    async def notif_full(self, message, titulo_embed, desc_embed, titulo_dm, desc_dm, user_id, motivo):
        embed = discord.Embed(title=titulo_embed, description=desc_embed, color=discord.Color.orange())
        await message.channel.send(content=message.author.mention, embed=embed, delete_after=NOTIF_TIEMPO)
        try:
            await message.author.send(embed=discord.Embed(title=titulo_dm, description=desc_dm, color=discord.Color.orange()))
        except:
            pass
        await registrar_falta(user_id, motivo)
        await log_discord(self.bot, f"❌ [GO-VIRAL] {message.author} — {motivo}", "warning", scope="go_viral")

    async def enviar_bienvenida(self, message):
        embed = discord.Embed(title=TITULO_BIENVENIDA, description=DESCRIPCION_BIENVENIDA, color=discord.Color.green())
        await message.channel.send(content=message.author.mention, embed=embed, delete_after=BIENVENIDA_TIEMPO)
        try:
            await message.author.send(embed=embed)
        except:
            pass

    async def obtener_publicaciones_previas(self, message, last_apoyo_id=None):
        mensajes = []
        found_last = False if last_apoyo_id else True
        async for msg in message.channel.history(before=message.created_at, limit=100, oldest_first=True):
            if msg.author.bot or msg.author.id == message.author.id:
                continue
            if not found_last:
                if str(msg.id) == str(last_apoyo_id):
                    found_last = True
                continue
            mensajes.append(msg)
        return mensajes

    def usuario_ya_apoyo(self, user_id, mensaje):
        key = f"go_viral:apoyos:{mensaje.id}"
        return self.redis.sismember(key, str(user_id))

    async def ultima_publicacion_y_turnos(self, message):
        ultima_pub = None
        turnos_entre = 0
        async for msg in message.channel.history(before=message.created_at, limit=100, oldest_first=False):
            if msg.author.id == message.author.id:
                ultima_pub = msg.created_at.replace(tzinfo=timezone.utc)
                break
            turnos_entre += 1
        return ultima_pub, turnos_entre

def limpiar_url_tweet(texto):
    """Devuelve la URL solo si está limpia."""
    match = re.search(r"https?://x\.com/\w+/status/(\d+)", texto)
    if match:
        usuario = re.search(r"https?://x\.com/([^/]+)/status", texto)
        if usuario:
            user = usuario.group(1)
            status_id = match.group(1)
            return f"https://x.com/{user}/status/{status_id}"
    return None

def extraer_url_tweet(texto):
    """Intenta encontrar una URL de tweet aunque esté en formato sucio."""
    url = re.findall(r"https?://x\.com/\S+", texto)
    if url:
        # Limpiar el final por si viene con parámetros o texto extra
        base = url[0].split("?")[0]
        # Si parece válida la retornamos, si no, None
        if re.match(r"https?://x\.com/\w+/status/\d+", base):
            return base
    return None

async def setup(bot):
    await bot.add_cog(GoViral(bot))
