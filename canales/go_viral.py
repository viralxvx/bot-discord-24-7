import discord
from discord.ext import commands
from config import CANAL_OBJETIVO_ID, EMOJIS_PERMITIDOS
from mensajes.viral_texto import (
    TITULO_APOYO_9_EDU, DESCRIPCION_APOYO_9_EDU,
    TITULO_INTERVALO_EDU, DESCRIPCION_INTERVALO_EDU,
    TITULO_SIN_LIKE_EDU, DESCRIPCION_SIN_LIKE_EDU,
    TITULO_SOLO_URL_EDU, DESCRIPCION_SOLO_URL_EDU,
)
from canales.faltas import registrar_falta  # Asegúrate de que registrar_falta esté bien importada
from utils.logger import log_discord
from datetime import datetime, timezone
import asyncio
import re

# -------------------------------
# CONFIGURACIÓN DE REGLAS FÁCIL
# -------------------------------
MAX_APOYOS = 1        # Máximo de posts a apoyar antes de publicar
MIN_TURNOS = 2        # Turnos mínimos de espera antes de publicar otra vez
INTERVALO_HORAS = 24  # Horas máximas de espera si nadie publica (luego puedes publicar)

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
        # Limpieza de reacciones no permitidas al iniciar (últimos 100 mensajes)
        bot.loop.create_task(self.limpiar_reacciones_no_permitidas())

    async def limpiar_reacciones_no_permitidas(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [GO-VIRAL] No se encontró el canal para limpiar reacciones.", "error", scope="go_viral")
            return
        await log_discord(self.bot, "🔄 [GO-VIRAL] Limpiando reacciones no permitidas en los últimos mensajes...", "info", scope="go_viral")
        try:
            async for msg in canal.history(limit=100, oldest_first=False):
                for reaction in msg.reactions:
                    if str(reaction.emoji) not in EMOJIS_PERMITIDOS:
                        async for user in reaction.users():
                            if not user.bot:
                                try:
                                    await reaction.remove(user)
                                except Exception:
                                    pass
            await log_discord(self.bot, "✅ [GO-VIRAL] Reacciones no permitidas eliminadas.", "success", scope="go_viral")
        except Exception as e:
            await log_discord(self.bot, f"❌ [GO-VIRAL] Error limpiando reacciones: {e}", "error", scope="go_viral")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != CANAL_OBJETIVO_ID:
            return

        user_id = str(message.author.id)

        # 1️⃣ Verifica formato de URL
        url = limpiar_url_tweet(message.content)
        if not url:
            await message.delete()
            embed = discord.Embed(
                title=TITULO_SOLO_URL_EDU,
                description=DESCRIPCION_SOLO_URL_EDU.format(usuario=message.author.mention),
                color=discord.Color.red()
            )
            try:
                await message.author.send(embed=embed)
            except:
                pass
            await log_discord(self.bot, f"❌ [GO-VIRAL] Mensaje de {message.author} eliminado: URL inválida.", "warning", scope="go_viral")
            await registrar_falta(user_id, "Formato incorrecto de publicación")
            return

        # 2️⃣ Verifica apoyos a publicaciones anteriores (máximo MAX_APOYOS)
        posts_previos = await self.obtener_publicaciones_previas(message)
        posts_a_apoyar = posts_previos[-MAX_APOYOS:]
        apoyos_ok = True
        for post in posts_a_apoyar:
            if not await self.usuario_ya_apoyo(message.author, post):
                apoyos_ok = False
                break

        if not apoyos_ok:
            await message.delete()
            embed = discord.Embed(
                title=TITULO_APOYO_9_EDU,
                description=DESCRIPCION_APOYO_9_EDU.format(usuario=message.author.mention),
                color=discord.Color.orange()
            )
            try:
                await message.author.send(embed=embed)
            except:
                pass
            await registrar_falta(user_id, "No apoyar publicaciones anteriores")
            await log_discord(self.bot, f"❌ [GO-VIRAL] {message.author} publicó sin apoyar los anteriores.", "warning", scope="go_viral")
            return

        # 3️⃣ Verifica intervalos de turnos/horas
        ultima_pub, turnos_entre = await self.ultima_publicacion_y_turnos(message)
        ahora = datetime.now(timezone.utc)
        horas_desde_ultima = (ahora - ultima_pub).total_seconds() / 3600 if ultima_pub else None

        if (turnos_entre < MIN_TURNOS) and (horas_desde_ultima is None or horas_desde_ultima < INTERVALO_HORAS):
            await message.delete()
            embed = discord.Embed(
                title=TITULO_INTERVALO_EDU,
                description=DESCRIPCION_INTERVALO_EDU.format(usuario=message.author.mention),
                color=discord.Color.orange()
            )
            try:
                await message.author.send(embed=embed)
            except:
                pass
            await registrar_falta(user_id, "No respetar intervalo de publicaciones")
            await log_discord(self.bot, f"❌ [GO-VIRAL] {message.author} publicó sin esperar el turno o tiempo.", "warning", scope="go_viral")
            return

        # 4️⃣ Espera 2 minutos para validación con 👍
        await asyncio.sleep(120)
        try:
            mensaje = await message.channel.fetch_message(message.id)
        except:
            # Ya fue eliminado o no se encuentra
            return
        validado = False
        for reaction in mensaje.reactions:
            if str(reaction.emoji) == "👍":
                async for user in reaction.users():
                    if user.id == message.author.id:
                        validado = True
                        break
        if not validado:
            await mensaje.delete()
            embed = discord.Embed(
                title=TITULO_SIN_LIKE_EDU,
                description=DESCRIPCION_SIN_LIKE_EDU.format(usuario=message.author.mention),
                color=discord.Color.red()
            )
            try:
                await message.author.send(embed=embed)
            except:
                pass
            await registrar_falta(user_id, "No validar publicación con 👍 en 2 minutos")
            await log_discord(self.bot, f"❌ [GO-VIRAL] {message.author} no validó con 👍 en 2 minutos.", "warning", scope="go_viral")
            return

        # 5️⃣ Si pasa todo, post válido
        await log_discord(self.bot, f"✅ [GO-VIRAL] Mensaje válido de {message.author}: {url}", "info", scope="go_viral")
        await self.bot.process_commands(message)

    # ------------ AUXILIARES ------------
    async def obtener_publicaciones_previas(self, message):
        """
        Devuelve una lista de los mensajes válidos anteriores a este mensaje en el canal,
        excluyendo los del propio autor, ordenados del más antiguo al más reciente.
        """
        mensajes = []
        async for msg in message.channel.history(before=message.created_at, limit=100, oldest_first=True):
            if msg.author.bot or msg.author.id == message.author.id:
                continue
            mensajes.append(msg)
        return mensajes

    async def usuario_ya_apoyo(self, usuario, mensaje):
        """
        Devuelve True si el usuario ya reaccionó con 🔥 a ese mensaje.
        """
        for reaction in mensaje.reactions:
            if str(reaction.emoji) == "🔥":
                async for user in reaction.users():
                    if user.id == usuario.id:
                        return True
        return False

    async def ultima_publicacion_y_turnos(self, message):
        """
        Devuelve (fecha de última publicación del usuario, cantidad de posts válidos entre la última y la actual)
        """
        ultima_pub = None
        turnos_entre = 0
        async for msg in message.channel.history(before=message.created_at, limit=100, oldest_first=False):
            if msg.author.id == message.author.id:
                ultima_pub = msg.created_at.replace(tzinfo=timezone.utc)
                break
            turnos_entre += 1
        return ultima_pub, turnos_entre

async def setup(bot):
    await bot.add_cog(GoViral(bot))
