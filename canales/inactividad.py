import discord
from discord.ext import commands, tasks
import os
import asyncio
import redis
from datetime import datetime, timedelta, timezone
from config import CANAL_OBJETIVO_ID, REDIS_URL, CANAL_FALTAS_ID, CANAL_LOGS_ID
from mensajes.inactividad_texto import AVISO_BANEO, AVISO_EXPULSION

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
        for guild in guilds:
            canal_faltas = self.bot.get_channel(CANAL_FALTAS_ID)
            canal_logs = self.bot.get_channel(CANAL_LOGS_ID)
            for member in guild.members:
                if member.bot or member.guild_permissions.administrator or member.guild_permissions.manage_guild:
                    continue

                user_id = str(member.id)
                key_actividad = f"inactividad:{user_id}"
                key_ban = f"inactividad:ban:{user_id}"
                key_expulsado = f"inactividad:expulsado:{user_id}"

                ultima_fecha_iso = self.redis.get(key_actividad)
                if not ultima_fecha_iso:
                    continue

                ultima_fecha = datetime.fromisoformat(ultima_fecha_iso)
                ahora = datetime.now(timezone.utc)
                dias_inactivo = (ahora - ultima_fecha).days

                # Si ya fue expulsado antes, no hacer nada más
                if self.redis.get(key_expulsado):
                    continue

                # Reincidencia: si ya estuvo baneado y volvió a estar 3 días inactivo, expulsar
                fecha_ban_iso = self.redis.get(key_ban)
                if fecha_ban_iso:
                    fecha_ban = datetime.fromisoformat(fecha_ban_iso)
                    # Si ya pasaron los 7 días del baneo, puede volver al servidor (debe hacerlo manual)
                    # Si vuelve y reincide, expulsar
                    if dias_inactivo >= DIAS_LIMITE_INACTIVIDAD:
                        try:
                            await guild.kick(member, reason="Expulsión automática: reincidencia por inactividad")
                            self.redis.set(key_expulsado, ahora.isoformat())
                            print(f"❌ [INACTIVIDAD] Usuario {member.display_name} ({user_id}) EXPULSADO por reincidencia.")
                            # DM
                            try:
                                await member.send(AVISO_EXPULSION)
                            except Exception as e:
                                print(f"⚠️ [INACTIVIDAD] No se pudo enviar DM de expulsión a {member.display_name}: {e}")
                            # Canal faltas/logs
                            if canal_faltas:
                                await canal_faltas.send(f"❌ Usuario expulsado por reincidir en inactividad: {member.mention}")
                            if canal_logs:
                                await canal_logs.send(f"❌ [INACTIVIDAD] Usuario expulsado por reincidir en inactividad: {member.mention} ({user_id})")
                        except Exception as e:
                            print(f"❌ [INACTIVIDAD] Error expulsando a {member.display_name}: {e}")
                    continue

                # Si nunca ha sido baneado pero está inactivo, baneo normal
                if dias_inactivo >= DIAS_LIMITE_INACTIVIDAD:
                    if not self.redis.get(key_ban):
                        try:
                            await guild.ban(member, reason="Inactividad: más de 3 días sin publicar")
                            self.redis.set(key_ban, ahora.isoformat())
                            print(f"🚫 [INACTIVIDAD] Usuario {member.display_name} ({user_id}) baneado por inactividad.")
                            # DM
                            try:
                                await member.send(AVISO_BANEO)
                            except Exception as e:
                                print(f"⚠️ [INACTIVIDAD] No se pudo enviar DM a {member.display_name}: {e}")
                            # Canal faltas/logs
                            if canal_faltas:
                                await canal_faltas.send(f"🚫 Usuario baneado automáticamente por inactividad: {member.mention}")
                            if canal_logs:
                                await canal_logs.send(f"🚫 [INACTIVIDAD] Usuario baneado por inactividad: {member.mention} ({user_id})")
                        except Exception as e:
                            print(f"❌ [INACTIVIDAD] Error baneando a {member.display_name}: {e}")

        print("✅ [INACTIVIDAD] Verificación automática completada.")

def setup(bot):
    bot.add_cog(Inactividad(bot))
