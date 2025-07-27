# canales/importar_pdf.py
import discord
from discord.ext import commands
import os
from mensajes.pdf_mensajes import mensaje_anclado_pdf

try:
    from utils.logger import custom_log
    usar_logger = True
except:
    usar_logger = False

CANAL_IMPORTAR_PDF = int(os.getenv("CANAL_IMPORTAR_PDF"))

class ImportarPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.publicar_mensaje_anclado())

    async def publicar_mensaje_anclado(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_IMPORTAR_PDF)
        if not canal:
            log("ERROR", "❌ Canal de importación PDF no encontrado.")
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
            log("INFO", "📌 Mensaje anclado correctamente en canal de importación PDF.")
        except Exception as e:
            log("ERROR", f"❌ Error al fijar mensaje PDF: {e}")

def log(nivel, mensaje):
    if usar_logger:
        try:
            custom_log(nivel, mensaje)
        except Exception as err:
            print(f"[LOGGER ERROR] {nivel}: {mensaje} | Fallo: {err}")
    else:
        print(f"[{nivel}] {mensaje}")

async def setup(bot):
    await bot.add_cog(ImportarPDF(bot))
