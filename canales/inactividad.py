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
        await log_discord(self.bot, "🔎 [INACTIVIDAD] Escaneando TODO el historial en 🧵go-viral...", CANAL_LOGS_ID, "info", "Inactividad")
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, f"❌ [INACTIVIDAD] No se encontró el canal 🧵go-viral (ID {CANAL_OBJETIVO_ID})", CANAL_LOGS_ID, "error", "Inactividad")
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
            await log_discord(self.bot, f"🔢 [INACTIVIDAD] Usuarios únicos detectados: {len(ultimos_mensajes)}", CANAL_LOGS_ID, "info", "Inactividad")
            for user_id, fecha in ultimos_mensajes.items():
                fecha_iso = fecha.astimezone(timezone.utc).isoformat()
                self.redis.set(f"inactividad:{user_id}", fecha_iso)
                await log_discord(self.bot, f"✅ [INACTIVIDAD] Usuario {user_id} — Última actividad: {fecha_iso}", CANAL_LOGS_ID, "success", "Inactividad")
            await log_discord(self.bot, "✅ [INACTIVIDAD] Registro de actividad inicial completado.", CANAL_LOGS_ID, "success", "Inactividad")
        except Exception as e:
            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error escaneando mensajes: {e}", CANAL_LOGS_ID, "error", "Inactividad")

    @tasks.loop(hours=6)
    async def verificar_inactivos(self):
        await self.bot.wait_until_ready()
        await log_discord(self.bot, "⏰ [INACTIVIDAD] Ejecutando verificación automática de inactivos...", CANAL_LOGS_ID, "info", "Inactividad")

        ahora = datetime.now(timezone.utc)

        for guild in self.bot.guilds:
            canal_faltas = self.bot.get_channel(CANAL_FALTAS_ID)
            canal_logs = self.bot.get_channel(CANAL_LOGS_ID)

            # 1. Revisión de baneos vencidos
            async for ban_entry in guild.bans():  # <-- Cambio aquí para utilizar async for
                user = ban_entry.user
                key_ban = f"inactividad:ban:{user.id}"
                ban_fecha_iso = self.redis.get(key_ban)
                if ban_fecha_iso:
                    ban_fecha = datetime.fromisoformat(ban_fecha_iso)
                    if (ahora - ban_fecha).days >= DURACION_BANEO_DIAS:
                        try:
                            await guild.unban(user, reason="Baneo de inactividad vencido, reintegrado automáticamente")
                            self.redis.delete(key_ban)
                            self.redis.hset(f"usuario:{user.id}", "estado", "activo")
                            await log_discord(self.bot, f"🔓 [INACTIVIDAD] Usuario {user} ({user.id}) desbaneado automáticamente tras 7 días.", CANAL_LOGS_ID, "success", "Inactividad")
                            try:
                                await user.send("🔓 Tu baneo por inactividad ha vencido y ya puedes volver a la comunidad. ¡Sé más activo para evitar nuevas sanciones!")
                            except Exception as e:
                                await log_discord(self.bot, f"⚠️ [INACTIVIDAD] No se pudo enviar DM de desbaneo a {user}: {e}", CANAL_LOGS_ID, "warning", "Inactividad")
                            if canal_faltas:
                                await canal_faltas.send(f"🔓 Usuario desbaneado automáticamente tras 7 días de inactividad: {user.mention}")
                            if canal_logs:
                                await canal_logs.send(f"🔓 [INACTIVIDAD] Usuario desbaneado tras 7 días: {user.mention} ({user.id})")
                        except Exception as e:
                            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error al desbanear a {user}: {e}", CANAL_LOGS_ID, "error", "Inactividad")

            # Limpieza de prórrogas vencidas y demás tareas siguen igual...

        await log_discord(self.bot, "✅ [INACTIVIDAD] Verificación automática completada.", CANAL_LOGS_ID, "success", "Inactividad")

async def setup(bot):
    await bot.add_cog(Inactividad(bot))
