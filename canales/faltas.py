import discord
from discord.ext import commands
import os
import asyncio
from config import CANAL_FALTAS_ID, REDIS_URL
import redis
from datetime import datetime, timedelta
import pytz

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.inicializar_panel_faltas())

    async def inicializar_panel_faltas(self):
        await self.bot.wait_until_ready()
        print("⚙️ Iniciando módulo de faltas...")

        canal = self.bot.get_channel(CANAL_FALTAS_ID)
        if not canal:
            print("❌ Error: no se encontró el canal de faltas.")
            return

        print("🔍 Cargando mensajes existentes del canal #📤faltas...")
        try:
            mensajes_existentes = [msg async for msg in canal.history(limit=None)]
        except Exception as e:
            print(f"❌ Error al cargar mensajes existentes: {e}")
            return

        print("🧹 Borrando todos los mensajes del canal...")
        try:
            await canal.purge(limit=None)
            print("✅ Canal limpiado con éxito.")
        except Exception as e:
            print(f"❌ Error al limpiar el canal: {e}")
            return

        print("📊 Reconstruyendo panel público de faltas...")
        try:
            guild = canal.guild
            for miembro in guild.members:
                if miembro.bot:
                    continue
                await self.publicar_o_actualizar_faltas(canal, miembro)
            print("✅ Panel público actualizado.")
        except Exception as e:
            print(f"❌ Error al reconstruir el panel: {e}")

    async def publicar_o_actualizar_faltas(self, canal, miembro):
        user_id = str(miembro.id)

        # Cargar datos del usuario (si existieran en Redis)
        total_faltas = int(self.redis.get(f"faltas:{user_id}:total") or 0)
        faltas_mes = int(self.redis.get(f"faltas:{user_id}:mes") or 0)
        estado = self.redis.get(f"faltas:{user_id}:estado") or "✅ Activo"

        embed = discord.Embed(title=f"📤 REGISTRO DE {miembro.mention}", color=discord.Color.orange())
        embed.set_author(name=f"{miembro.display_name}", icon_url=miembro.display_avatar.url)
        embed.add_field(name="Estado actual", value=estado, inline=False)
        embed.add_field(name="Total de faltas", value=str(total_faltas), inline=False)
        embed.add_field(name="Faltas este mes", value=str(faltas_mes), inline=False)

        hora_actual = datetime.now(pytz.timezone('America/Santo_Domingo'))
        hora_formateada = hora_actual.strftime('%A a las %H:%M').capitalize()
        embed.set_footer(text=f"Sistema automatizado de reputación pública • {hora_formateada}")

        try:
            await canal.send(embed=embed)
        except Exception as e:
            print(f"❌ Error al enviar mensaje de {miembro.display_name}: {e}")


def setup(bot):
    bot.add_cog(Faltas(bot))
