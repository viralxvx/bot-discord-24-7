import discord
from discord.ext import commands, tasks
import redis
from datetime import datetime, timedelta, timezone
from config import CANAL_OBJETIVO_ID, REDIS_URL, CANAL_FALTAS_ID, CANAL_LOGS_ID
from mensajes.inactividad_texto import AVISO_BANEO, AVISO_EXPULSION, PRORROGA_CONCEDIDA

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
        print("🔎 [INACTIVIDAD] Iniciando escaneo de actividad en 🧵go-viral...")
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            print(f"❌ [INACTIVIDAD] No se encontró el canal 🧵go-viral (ID {CANAL_OBJETIVO_ID})")
            return

        ultimos_mensajes = {}
        try:
            async for mensaje in canal.history(limit=1000, oldest_first=False):
                autor = mensaje.author
                if autor.bot:
                    continue
                user_id = str(autor.id)
                if user_id not in ultimos_mensajes or mensaje.created_at > ultimos_mensajes[user_id]:
                    ultimos_mensajes[user_id] = mensaje.created_at
            print(f"🔢 [INACTIVIDAD] Usuarios únicos detectados: {len(ultimos_mensajes)}")
            for user_id, fecha in ultimos_mensajes.items():
                fecha_iso = fecha.astimezone(timezone.utc).isoformat()
                self.redis.set(f"inactividad:{user_id}", fecha_iso)
                print(f"✅ [INACTIVIDAD] Usuario {user_id} — Última actividad: {fecha_iso}")
            print("✅ [INACTIVIDAD] Registro de actividad inicial completado.")
        except Exception as e:
            print(f"❌ [INACTIVIDAD] Error escaneando mensajes: {e}")

    @tasks.loop(hours=6)
    async def verificar_inactivos(self):
        await self.bot.wait_until_ready()
        print("⏰ [INACTIVIDAD] Ejecutando verificación automática de inactivos...")

        guilds = self.bot.guilds
        ahora = datetime.now(timezone.utc)

        for guild in guilds:
            canal_faltas = self.bot.get_channel(CANAL_FALTAS_ID)
            canal_logs = self.bot.get_channel(CANAL_LOGS_ID)

            # 1. Revisión de baneos vencidos (limpieza y reintegración automática)
            for ban_entry in await guild.bans():
                user = ban_entry.user
                key_ban = f"inactividad:ban:{user.id}"
                ban_fecha_iso = self.redis.get(key_ban)
                if ban_fecha_iso:
                    ban_fecha = datetime.fromisoformat(ban_fecha_iso)
                    if (ahora - ban_fecha).days >= DURACION_BANEO_DIAS:
                        # El baneo ha vencido, desbanear y limpiar estado
                        try:
                            await guild.unban(user, reason="Baneo de inactividad vencido, reintegrado automáticamente")
                            self.redis.delete(key_ban)
                            print(f"🔓 [INACTIVIDAD] Usuario {user} ({user.id}) desbaneado automáticamente tras 7 días.")
                            try:
                                await user.send("🔓 Tu baneo por inactividad ha vencido y ya puedes volver a la comunidad. ¡Sé más activo para evitar nuevas sanciones!")
                            except Exception as e:
                                print(f"⚠️ [INACTIVIDAD] No se pudo enviar DM de desbaneo a {user}: {e}")
                            if canal_faltas:
                                await canal_faltas.send(f"🔓 Usuario desbaneado automáticamente tras 7 días de inactividad: {user.mention}")
                            if canal_logs:
                                await canal_logs.send(f"🔓 [INACTIVIDAD] Usuario desbaneado tras 7 días: {user.mention} ({user.id})")
                        except Exception as e:
                            print(f"❌ [INACTIVIDAD] Error al desbanear a {user}: {e}")

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
                        print(f"🧹 [INACTIVIDAD] Prórroga vencida y eliminada para {member.display_name} ({member.id})")

            # 3. Lógica de baneos/expulsiones normales (idéntico a la fase 5, no lo repito aquí...)

        print("✅ [INACTIVIDAD] Verificación automática completada.")

def setup(bot):
    bot.add_cog(Inactividad(bot))
