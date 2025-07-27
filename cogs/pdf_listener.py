# cogs/pdf_listener.py
import discord
from discord.ext import commands
import os
import tempfile

from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.export_csv import exportar_contactos_csv
from utils.gofile import subir_a_gofile
from utils.logger import custom_log
from utils.discord_tools import crear_mensaje_progreso, actualizar_mensaje_progreso
from utils.progreso import generar_barra_progreso

CANAL_IMPORTAR_PDF = int(os.getenv("CANAL_IMPORTAR_PDF"))

class PDFListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != CANAL_IMPORTAR_PDF or message.author.bot:
            return

        for archivo in message.attachments:
            if archivo.filename.lower().endswith(".pdf"):
                await self.procesar_pdf(message, archivo)

    async def procesar_pdf(self, message, archivo):
        user_id = str(message.author.id)
        canal = message.channel

        progreso_msg = await crear_mensaje_progreso(canal, "Procesando PDF...")

        try:
            # Guardar archivo en ruta temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                ruta_pdf = tmp.name

            await archivo.save(ruta_pdf)  # ✅ GUARDAMOS USANDO LA RUTA, NO EL OBJETO tmp

            async def actualizar_progreso(p):
                barra = generar_barra_progreso(p)
                await actualizar_mensaje_progreso(progreso_msg, f"[Activo] ✅ Progreso: {barra} {p}%")

            contactos = await extraer_contactos_desde_pdf(
                ruta_pdf,
                user_id,
                progreso_callback=actualizar_progreso
            )

            if not contactos:
                await actualizar_mensaje_progreso(progreso_msg, "⚠️ No se encontraron contactos válidos.")
                return

            ruta_csv = exportar_contactos_csv(archivo.filename, user_id, contactos)
            url_csv = await subir_a_gofile(ruta_csv)

            embed = discord.Embed(title="✅ PDF procesado con éxito", color=0x2ecc71)
            embed.add_field(name="📄 Archivo original", value=archivo.filename, inline=False)
            embed.add_field(name="👥 Contactos extraídos", value=f"{len(contactos):,}", inline=True)
            embed.add_field(name="⬇️ Descargar CSV", value=url_csv, inline=False)
            embed.set_footer(text="Gracias por usar VXbot | Profesional ✨")

            await progreso_msg.edit(content=None, embed=embed)
            custom_log(self.bot, "LISTENER_PDF", "INFO", f"✅ PDF procesado desde mensaje: {archivo.filename}")

        except Exception as e:
            await progreso_msg.edit(content=f"❌ Error al procesar PDF desde mensaje: {e}")
            custom_log(self.bot, "LISTENER_PDF", "ERROR", f"❌ Error al procesar PDF desde mensaje: {e}")

async def setup(bot):
    await bot.add_cog(PDFListener(bot))
