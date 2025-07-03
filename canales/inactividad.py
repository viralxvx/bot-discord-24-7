import discord
from discord.ext import commands
import os
import asyncio
import redis
from datetime import datetime, timezone, timedelta
from config import CANAL_OBJETIVO_ID, REDIS_URL

class Inactividad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.registrar_actividad())

    async def registrar_actividad(self):
        await self.bot.wait_until_ready()
        print("🔎 [INACTIVIDAD] Iniciando escaneo de actividad en 🧵go-viral...")
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            print(f"❌ [INACTIVIDAD] No se encontró el canal 🧵go-viral (ID {CANAL_OBJETIVO_ID})")
            return

        # Diccionario para guardar el último mensaje de cada miembro
        ultimos_mensajes = {}

        try:
            # Recorrer los mensajes más recientes (puedes ajustar el límite si tienes muchísima historia)
            async for mensaje in canal.history(limit=1000, oldest_first=False):
                autor = mensaje.author
                if autor.bot:
                    continue
                user_id = str(autor.id)
                # Solo guarda el más reciente
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

def setup(bot):
    bot.add_cog(Inactividad(bot))
