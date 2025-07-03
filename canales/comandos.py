# canales/comandos.py

import discord
from discord.ext import commands
import os
from mensajes.comandos_texto import INSTRUCCIONES_COMANDOS

CANAL_COMANDOS = int(os.getenv("CANAL_COMANDOS"))

class CanalComandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("⚙️ Iniciando módulo de comandos...")

        canal = self.bot.get_channel(CANAL_COMANDOS)
        if not canal:
            print(f"❌ Error: No se encontró el canal de comandos con ID {CANAL_COMANDOS}")
            return

        try:
            async for msg in canal.history(limit=100):
                if msg.author == self.bot.user:
                    await msg.delete()
            await canal.send(INSTRUCCIONES_COMANDOS)
            print("✅ Mensaje de instrucciones enviado en canal de comandos.")
        except Exception as e:
            print(f"❌ Error al enviar el mensaje de instrucciones: {e}")

async def setup(bot):
    await bot.add_cog(CanalComandos(bot))
