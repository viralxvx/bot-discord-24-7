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
    TITULO_INTERVALO_DM, DESCRIPCION_INTERVALO_DM
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
        bot.loop.create_task(self.init_mensaje_fijo())

    async def init_mensaje_fijo(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            print(f"❌ [GO-VIRAL] No se encontró el canal (ID {CANAL_OBJETIVO_ID})")
            return
        async for msg in canal.history(limit=20, oldest_first=True):
            # Compara por título en embed, no por texto plano
            if msg.author == self.bot.user and msg.embeds:
                embed = msg.embeds[0]
                if embed.title and "GO-VIRAL" in embed.title:
                    print("✅ [GO-VIRAL] Mensaje fijo ya existe.")
                    return
        fecha = datetime.now().strftime("%Y-%m-%d")
        embed = discord.Embed(
            title=TITULO_FIJO,
            description=DESCRIPCION_FIJO.format(fecha=fecha),
            color=discord.Color.blurple()
        )
        embed.set_image(url=IMAGEN_URL)
        msg = await canal.send(embed=embed)
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
                # Educativo en canal (embed)
                embed = discord.Embed(
                    title=TITULO_URL_EDU,
                    description=DESCRIPCION_URL_EDU,
                    color=discord.Color.orange()
                )
                try:
                    await message.channel.send(embed=embed, delete_after=15)
                except: pass
                # DM educativo (embed)
                embed_dm = discord.Embed(
                    title=TITULO_URL_DM,
                    description=DESCRIPCION_URL_DM.format(usuario=message.author.display_name),
                    color=discord.Color.orange()
                )
                try:
                    await message.author.send(embed=embed_dm)
                except: pass
                return

        # --- Control de intervalo entre publicaciones ---
        if not await self.verificar_intervalo_entre_publicaciones(message):
            return  # Si falla, ya notificó y borró el mensaje

        # --- Verificación de apoyo a los 9 anteriores ---
        if not await self.verificar_apoyo_nueve_anteriores(message):
            return  # Si falla, ya notificó y borró el mensaje

        # Inicia verificación de reacción 👍 del autor a su propio mensaje
        self.bot.loop.create_task(self.verificar_reaccion_like(message))

    async def verificar_intervalo_entre_publicaciones(self, message):
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
        mensajes.reverse()  # De más antiguos a más nuevos

        idx = None
        for i, msg in enumerate(mensajes):
            if msg.id == message.id:
                idx = i
                break
        if idx is None or idx < 9:
            return True  # Primer post del usuario o poco historial

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
