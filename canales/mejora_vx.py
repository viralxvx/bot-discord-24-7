# canales/mejora_vx.py

import discord
from discord.ext import commands
from config import CANAL_MEJORA_VX_ID
from mensajes.mejora_vx_mensaje import MENSAJE_ANCLADO
from utils.logger import log_error, log_success

class MejoraVX(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def limpiar_y_anclar_mensaje(self):
        try:
            canal = await self.bot.fetch_channel(CANAL_MEJORA_VX_ID)
        except Exception as e:
            await log_error(f"No se pudo acceder al canal mejora-vx: {e}", self.bot, scope="mejora_vx")
            return

        try:
            async for msg in canal.history(limit=100):
                await msg.delete()

            mensaje = await canal.send(MENSAJE_ANCLADO)
            await mensaje.pin()

            print("✅ Mensaje anclado publicado y fijado en 🧠┃mejora-vx.")
            await log_success("Mensaje fijo publicado y anclado correctamente.", self.bot, title="🧠 Mejora VX", scope="mejora_vx")

        except Exception as e:
            await log_error(f"❌ Error al limpiar o fijar mensaje en mejora-vx: {e}", self.bot, scope="mejora_vx")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.limpiar_y_anclar_mensaje()

async def setup(bot):
    await bot.add_cog(MejoraVX(bot))
