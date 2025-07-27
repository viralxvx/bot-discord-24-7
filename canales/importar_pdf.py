# canales/importar_pdf.py
import discord
from discord.ext import commands
import os
from mensajes.pdf_mensajes import mensaje_anclado_pdf
from utils.logger import custom_log

CANAL_IMPORTAR_PDF = int(os.getenv("CANAL_IMPORTAR_PDF"))

class ImportarPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.publicar_mensaje_anclado())

    async def publicar_mensaje_anclado(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_IMPORTAR_PDF)
        if not canal:
            custom_log("❌ Canal de importación PDF no encontrado.")
            return

        try:
            mensajes = [m async for m in canal.history(limit=50)]
            for m in mensajes:
                try:
                    await m.unpin()
                    await m.delete()
                except:
                    continue

            mensaje = await canal.send(mensaje_anclado_pdf())
            await mensaje.pin()
            custom_log("📌 Mensaje anclado en canal de importación PDF.")
        except Exception as e:
            custom_log(f"❌ Error al fijar mensaje PDF: {e}")

async def setup(bot):
    await bot.add_cog(ImportarPDF(bot))
