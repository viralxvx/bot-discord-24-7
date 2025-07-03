import discord
from discord.ext import commands
import os

CANAL_COMANDOS_ID = 1390164280959303831  # 💻comandos

class CanalComandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        canal = self.bot.get_channel(CANAL_COMANDOS_ID)
        if not canal:
            print("❌ No se encontró el canal 💻comandos.")
            return

        try:
            mensajes = [msg async for msg in canal.history(limit=20)]
            ya_publicado = any("📌 COMANDOS DISPONIBLES" in msg.content for msg in mensajes if msg.author == self.bot.user)

            if not ya_publicado:
                await canal.send(
                    "**📌 COMANDOS DISPONIBLES EN ESTE CANAL**\n\n"
                    "➡️ `/estado`: Consulta tu estado actual (faltas, sanciones, situación).\n"
                    "➡️ `/estadísticas`: Muestra estadísticas generales del servidor.\n\n"
                    "⚠️ Solo los administradores pueden usar `/estadísticas`.\n"
                    "⏳ Las respuestas aquí durarán 10 minutos y también serán enviadas por DM."
                )
                print("✅ Instrucciones publicadas en el canal 💻comandos.")
            else:
                print("ℹ️ Instrucciones ya publicadas previamente.")
        except Exception as e:
            print(f"❌ Error al enviar instrucciones: {e}")

async def setup(bot):
    await bot.add_cog(CanalComandos(bot))
