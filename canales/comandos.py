import discord
from discord.ext import commands
import logging
import os
from config import CANAL_COMANDOS_ID
from mensajes.comandos_texto import INSTRUCCIONES_COMANDOS

class CanalComandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        bot.loop.create_task(self.configurar_canal_comandos())

    async def configurar_canal_comandos(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_COMANDOS_ID)

        if not canal:
            self.logger.error("❌ No se encontró el canal de comandos.")
            return

        self.logger.info("🛠️ Configurando canal de comandos...")

        try:
            await canal.purge(limit=None)
            self.logger.info("🧹 Canal de comandos limpiado correctamente.")
        except Exception as e:
            self.logger.error(f"❌ Error al limpiar el canal de comandos: {e}")
            return

        try:
            await canal.send(INSTRUCCIONES_COMANDOS)
            self.logger.info("✅ Instrucciones de uso enviadas al canal de comandos.")
        except Exception as e:
            self.logger.error(f"❌ Error al enviar instrucciones al canal de comandos: {e}")

def setup(bot):
    bot.add_cog(CanalComandos(bot))
