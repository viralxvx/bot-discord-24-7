import discord
from discord.ext import commands, tasks
import os
import asyncio
import redis
from datetime import datetime, timedelta, timezone
from config import CANAL_OBJETIVO_ID, REDIS_URL
from mensajes.inactividad_texto import AVISO_BANEO

DIAS_LIMITE_INACTIVIDAD = 3  # Días sin publicar para aplicar baneo
DURACION_BANEO_DIAS = 7      # Duración del baneo automático

class Inactividad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.registrar_actividad())
        self.verificar_inactivos.start()  # ← inicia la tarea periódica

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
            for member in guild.members:
                if member.bot or member.guild_permissions.administrator or member.guild_permissions.manage_guild:
                    continue  # Ignora bots y admins

                user_id = str(member.id)
                key_actividad = f"inactividad:{user_id}"
                ultima_fecha_iso = self.redis.get(key_actividad)
                if not ultima_fecha_iso:
                    continue  # Nunca ha publicado

                ultima_fecha = datetime.fromisoformat(ultima_fecha_iso)
                ahora = datetime.now(timezone.utc)
                dias_inactivo = (ahora - ultima_fecha).days

                # Verifica si ya fue baneado antes
                key_ban = f"inactividad:ban:{user_id}"
                if self.redis.get(key_ban):
                    continue

                # Prórrogas (fase siguiente), si quieres puedes ya añadir el placeholder:
                # key_prorroga = f"inactividad:prorroga:{user_id}"
                # if self.redis.get(key_prorroga):
                #     continue

                if dias_inactivo >= DIAS_LIMITE_INACTIVIDAD:
                    try:
                        # Baneo temporal
                        await guild.ban(member, reason="Inactividad: más de 3 días sin publicar")
                        self.redis.set(key_ban, ahora.isoformat())
                        print(f"🚫 [INACTIVIDAD] Usuario {member.display_name} ({user_id}) baneado por inactividad.")

                        # Mensaje directo al usuario
                        try:
                            await member.send(AVISO_BANEO)
                        except Exception as e:
                            print(f"⚠️ [INACTIVIDAD] No se pudo enviar DM a {member.display_name}: {e}")

                    except Exception as e:
                        print(f"❌ [INACTIVIDAD] Error baneando a {member.display_name}: {e}")

        print("✅ [INACTIVIDAD] Verificación automática completada.")

def setup(bot):
    bot.add_cog(Inactividad(bot))
