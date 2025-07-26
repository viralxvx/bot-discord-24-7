# canales/mejora_vx.py

import discord
from discord.ext import commands
import os
from config import CANAL_MEJORA_VX_ID
from mensajes.mejora_vx_mensaje import MENSAJE_ANCLADO
from utils.logger import log_error

class MejoraVX(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mensaje_anclado_id = None

    async def limpiar_y_anclar_mensaje(self):
        canal = self.bot.get_channel(CANAL_MEJORA_VX_ID)
        if not canal:
            print("❌ No se encontró el canal 🧠┃mejora-vx.")
            return

        # Eliminar todos los mensajes (incluyendo fijados)
        try:
            async for msg in canal.history(limit=100):
                await msg.delete()
        except Exception as e:
            log_error(f"Error al limpiar canal de mejora: {e}")

        try:
            mensaje = await canal.send(MENSAJE_ANCLADO)
            await mensaje.pin()
            self.mensaje_anclado_id = mensaje.id
            print("✅ Mensaje anclado publicado y fijado correctamente en 🧠┃mejora-vx.")
        except Exception as e:
            log_error(f"Error al publicar mensaje anclado de mejora: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.limpiar_y_anclar_mensaje()

async def setup(bot):
    await bot.add_cog(MejoraVX(bot))
