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
from datetime import datetime
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
        bot.loop.create_task(self.preload_historial_miembros())
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

    async def init_mensaje_fijo(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            print(f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})")
            return

        # Busca mensaje fijo existente (embed con título específico)
        mensaje_fijo_existente = None
        async for msg in canal.history(limit=30, oldest_first=True):
            if msg.author == self.bot.user and msg.embeds:
                embed = msg.embeds[0]
                if embed.title and embed.title == TITULO_FIJO:
                    mensaje_fijo_existente = msg
                    break

        fecha = datetime.now().strftime("%Y-%m-%d")
        embed_fijo = discord.Embed(
            title=TITULO_FIJO,
            description=DESCRIPCION_FIJO.format(fecha=fecha),
            color=discord.Color.blurple()
        )
        embed_fijo.set_image(url=IMAGEN_URL)

        # Si existe y es igual, no hace nada. Si existe pero cambió, edita. Si no existe, lo crea.
        if mensaje_fijo_existente:
            # ¿El contenido cambió?
            embed_actual = mensaje_fijo_existente.embeds[0]
            if (embed_actual.description != embed_fijo.description) or (embed_actual.image.url != IMAGEN_URL):
                await mensaje_fijo_existente.edit(embed=embed_fijo)
                print("🔄 [GO-VIRAL] Mensaje fijo actualizado.")
            else:
                print("✅ [GO-VIRAL] Mensaje fijo ya existe y está actualizado.")
        else:
            msg = await canal.send(embed=embed_fijo)
            await msg.pin()
            print("✅ [GO-VIRAL] Mensaje fijo publicado y fijado.")

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
            # Notificación en canal (embed, 15s)
            embed = discord.Embed(
                title=TITULO_SOLO_URL_EDU,
                description=DESCRIPCION_SOLO_URL_EDU.format(usuario=message.author.mention),
                color=discord.Color.red()
            )
            try:
                await message.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            # DM educativa
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
            self.bot.loop.create_task(self.verificar_reaccion_like(message))
            return

        # --- Control de intervalo entre publicaciones ---
        if not await self.verificar_intervalo_entre_publicaciones(message):
            return

        # --- Verificación de apoyo a los 9 anteriores ---
        if not await self.verificar_apoyo_nueve_anteriores(message):
            return

        # Inicia verificación de reacción 👍 del autor a su propio mensaje
        self.bot.loop.create_task(self.verificar_reaccion_like(message))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Permitir solo 👍 y 🔥 en el canal GO-VIRAL
        if reaction.message.channel.id != CANAL_OBJETIVO_ID or user.bot:
            return
        if str(reaction.emoji) not in ["🔥", "👍"]:
            try:
                await reaction.remove(user)
            except Exception:
                pass
            # Notifica en canal
            embed = discord.Embed(
                title=TITULO_SOLO_REACCION_EDU,
                description=DESCRIPCION_SOLO_REACCION_EDU.format(usuario=user.mention),
                color=discord.Color.red()
            )
            try:
                await reaction.message.channel.send(embed=embed, delete_after=15)
            except Exception:
                pass
            # DM educativa
            embed_dm = discord.Embed(
                title=TITULO_SOLO_REACCION_DM,
                description=DESCRIPCION_SOLO_REACCION_DM,
                color=discord.Color.red()
            )
            try:
                await user.send(embed=embed_dm)
            except Exception:
                pass

    # ... (mantén aquí las funciones verificar_intervalo_entre_publicaciones, verificar_apoyo_nueve_anteriores y verificar_reaccion_like sin cambios)

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
                print(f"❌ [GO-VIRAL] Publicación de {message.author.display_name} eliminada por INTERVALO insuficiente.")
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
        if idx is None or idx < 9:
            return True

        posts_previos = mensajes[idx-9:idx]
        apoyo_faltante = []
        for post in posts_previos:
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
            try:
                await message.delete()
                print(f"❌ [GO-VIRAL] Publicación de {message.author.display_name} eliminada por NO apoyar a los 9 anteriores.")
            except Exception as e:
                print(f"❌ [GO-VIRAL] Error eliminando mensaje (no apoyó a 9): {e}")
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
