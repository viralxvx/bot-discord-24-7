import discord
from discord.ext import commands, tasks
import redis
from datetime import datetime, timedelta, timezone
from config import CANAL_OBJETIVO_ID, REDIS_URL, CANAL_FALTAS_ID, CANAL_LOGS_ID
from mensajes.inactividad_texto import AVISO_BANEO, AVISO_EXPULSION, PRORROGA_CONCEDIDA
from utils.logger import log_discord  # <-- IMPORTANTE

DIAS_LIMITE_INACTIVIDAD = 3
DURACION_BANEO_DIAS = 7

class Inactividad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.registrar_actividad())
        self.verificar_inactivos.start()

    async def registrar_actividad(self):
        await self.bot.wait_until_ready()
        await log_discord(self.bot, "🔎 [INACTIVIDAD] Escaneando TODO el historial en 🧵go-viral...", "info", "Inactividad")
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, f"❌ [INACTIVIDAD] No se encontró el canal 🧵go-viral (ID {CANAL_OBJETIVO_ID})", "error", "Inactividad")
            return

        ultimos_mensajes = {}
        try:
            async for mensaje in canal.history(limit=None, oldest_first=False):
                autor = mensaje.author
                if autor.bot:
                    continue
                user_id = str(autor.id)
                if user_id not in ultimos_mensajes or mensaje.created_at > ultimos_mensajes[user_id]:
                    ultimos_mensajes[user_id] = mensaje.created_at
            await log_discord(self.bot, f"🔢 [INACTIVIDAD] Usuarios únicos detectados: {len(ultimos_mensajes)}", "info", "Inactividad")
            for user_id, fecha in ultimos_mensajes.items():
                fecha_iso = fecha.astimezone(timezone.utc).isoformat()
                self.redis.set(f"inactividad:{user_id}", fecha_iso)
                await log_discord(self.bot, f"✅ [INACTIVIDAD] Usuario {user_id} — Última actividad: {fecha_iso}", "success", "Inactividad")
            await log_discord(self.bot, "✅ [INACTIVIDAD] Registro de actividad inicial completado.", "success", "Inactividad")
        except Exception as e:
            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error escaneando mensajes: {e}", "error", "Inactividad")

    @tasks.loop(hours=6)
    async def verificar_inactivos(self):
        await self.bot.wait_until_ready()
        await log_discord(self.bot, "⏰ [INACTIVIDAD] Ejecutando verificación automática de inactivos...", "info", "Inactividad")

        ahora = datetime.now(timezone.utc)

        for guild in self.bot.guilds:
            canal_faltas = self.bot.get_channel(CANAL_FALTAS_ID)
            canal_logs = self.bot.get_channel(CANAL_LOGS_ID)

            # 1. Revisión de baneos vencidos
            try:
                async for ban_entry in guild.bans():
                    user = ban_entry.user
                    key_ban = f"inactividad:ban:{user.id}"
                    ban_fecha_iso = self.redis.get(key_ban)
                    if ban_fecha_iso:
                        ban_fecha = datetime.fromisoformat(ban_fecha_iso)
                        if (ahora - ban_fecha).days >= DURACION_BANEO_DIAS:
                            await guild.unban(user, reason="Baneo de inactividad vencido, reintegrado automáticamente")
                            self.redis.delete(key_ban)
                            self.redis.hset(f"usuario:{user.id}", "estado", "activo")
                            await log_discord(self.bot, f"🔓 [INACTIVIDAD] Usuario {user} ({user.id}) desbaneado automáticamente tras 7 días.", "success", "Inactividad")
                            try:
                                await user.send("🔓 Tu baneo por inactividad ha vencido y ya puedes volver a la comunidad. ¡Sé más activo para evitar nuevas sanciones!")
                            except Exception as e:
                                await log_discord(self.bot, f"⚠️ [INACTIVIDAD] No se pudo enviar DM de desbaneo a {user}: {e}", "warning", "Inactividad")
                            if canal_faltas:
                                await canal_faltas.send(f"🔓 Usuario desbaneado automáticamente tras 7 días de inactividad: {user.mention}")
                            if canal_logs:
                                await canal_logs.send(f"🔓 [INACTIVIDAD] Usuario desbaneado tras 7 días: {user.mention} ({user.id})")
            except Exception as e:
                await log_discord(self.bot, f"❌ [INACTIVIDAD] Error al obtener baneos: {e}", "error", "Inactividad")

            # 2. Limpieza de prórrogas vencidas
            for member in guild.members:
                if member.bot:
                    continue
                key_prorroga = f"inactividad:prorroga:{member.id}"
                prorroga_iso = self.redis.get(key_prorroga)
                if prorroga_iso:
                    fecha_prorroga = datetime.fromisoformat(prorroga_iso)
                    if ahora >= fecha_prorroga:
                        self.redis.delete(key_prorroga)
                        await log_discord(self.bot, f"🧹 [INACTIVIDAD] Prórroga vencida y eliminada para {member.display_name} ({member.id})", "info", "Inactividad")

            # 3. Baneo/expulsión por inactividad
            for member in guild.members:
                if member.bot:
                    continue

                key_prorroga = f"inactividad:prorroga:{member.id}"
                if self.redis.get(key_prorroga):
                    continue

                key_ban = f"inactividad:ban:{member.id}"
                if self.redis.get(key_ban):
                    continue

                key_inactividad = f"inactividad:{member.id}"
                last_post_iso = self.redis.get(key_inactividad)
                if not last_post_iso:
                    continue

                last_post = datetime.fromisoformat(last_post_iso)
                dias_inactivo = (ahora - last_post).days

                key_expulsado = f"inactividad:expulsado:{member.id}"
                if self.redis.get(key_expulsado):
                    continue

                key_reincidencia = f"inactividad:reincidencia:{member.id}"
                reincidencias = int(self.redis.get(key_reincidencia) or 0)

                if dias_inactivo >= DIAS_LIMITE_INACTIVIDAD:
                    if reincidencias == 0:
                        try:
                            await guild.ban(member, reason="Inactividad superior a 3 días (automatizado)", delete_message_days=0)
                            self.redis.set(key_ban, ahora.isoformat())
                            self.redis.incr(key_reincidencia)
                            self.redis.hset(f"usuario:{member.id}", "estado", "baneado")
                            await log_discord(self.bot, f"⛔ [INACTIVIDAD] Usuario {member} ({member.id}) baneado por inactividad.", "warning", "Inactividad")
                            try:
                                await member.send(AVISO_BANEO)
                            except Exception:
                                pass
                            if canal_faltas:
                                await canal_faltas.send(f"⛔ Usuario baneado automáticamente por inactividad: {member.mention}")
                            if canal_logs:
                                await canal_logs.send(f"⛔ [INACTIVIDAD] Usuario baneado: {member.mention} ({member.id})")
                        except Exception as e:
                            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error baneando a {member}: {e}", "error", "Inactividad")
                    else:
                        try:
                            await guild.kick(member, reason="Expulsión por inactividad reincidente (automatizado)")
                            self.redis.set(key_expulsado, "1")
                            self.redis.hset(f"usuario:{member.id}", "estado", "expulsado")
                            await log_discord(self.bot, f"🚫 [INACTIVIDAD] Usuario {member} ({member.id}) EXPULSADO por reincidencia de inactividad.", "error", "Inactividad")
                            try:
                                await member.send(AVISO_EXPULSION)
                            except Exception:
                                pass
                            if canal_faltas:
                                await canal_faltas.send(f"🚫 Usuario EXPULSADO permanentemente por reincidencia de inactividad: {member.mention}")
                            if canal_logs:
                                await canal_logs.send(f"🚫 [INACTIVIDAD] Usuario EXPULSADO: {member.mention} ({member.id})")
                        except Exception as e:
                            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error expulsando a {member}: {e}", "error", "Inactividad")

        await log_discord(self.bot, "✅ [INACTIVIDAD] Verificación automática completada.", "success", "Inactividad")

# =============== LISTENERS UNIVERSALES DE ESTADO ===============

class EstadoMiembros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.redis.hset(f"usuario:{user.id}", "estado", "baneado")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        self.redis.hset(f"usuario:{user.id}", "estado", "activo")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        expulsado = self.redis.get(f"inactividad:expulsado:{member.id}")
        if expulsado == "1":
            self.redis.hset(f"usuario:{member.id}", "estado", "expulsado")
        else:
            self.redis.hset(f"usuario:{member.id}", "estado", "desercion")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.redis.hset(f"usuario:{member.id}", "estado", "activo")

async def setup(bot):
    await bot.add_cog(Inactividad(bot))
    await bot.add_cog(EstadoMiembros(bot))
