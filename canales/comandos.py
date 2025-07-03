import discord
from discord.ext import commands
import os
from config import CANAL_COMANDOS_ID
from mensajes.comandos_texto import INSTRUCCIONES_COMANDOS

class CanalComandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.configurar_canal())

    async def configurar_canal(self):
        await self.bot.wait_until_ready()
        print("⚙️ Iniciando módulo del canal de comandos...")

        canal = self.bot.get_channel(CANAL_COMANDOS_ID)
        if not canal:
            print("❌ Error: no se encontró el canal de comandos.")
            return

        try:
            print("🧹 Limpiando mensajes antiguos del canal de comandos...")
            await canal.purge(limit=None)
            print("✅ Canal de comandos limpio.")

            await canal.send(INSTRUCCIONES_COMANDOS)
            print("📌 Instrucciones de uso enviadas.")
        except Exception as e:
            print(f"❌ Error al configurar el canal de comandos: {e}")

# 👉 Formato asincrónico requerido por discord.py 2.0+
async def setup(bot):
    await bot.add_cog(CanalComandos(bot))
