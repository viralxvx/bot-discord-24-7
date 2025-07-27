#cogs/pdf_listener.py
import discord
from discord.ext import commands
import os
import tempfile

from utils.logger import custom_log
from utils.gofile import subir_a_gofile
from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.export_csv import exportar_contactos_csv
from utils.progreso import generar_barra_progreso
from utils.discord_tools import limpiar_canal_despues

CANAL_IMPORTAR_PDF = int(os.getenv("CANAL_IMPORTAR_PDF"))

class PDFListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id != CANAL_IMPORTAR_PDF:
            return

        if not message.attachments:
            return

        archivo = message.attachments[0]
        if not archivo.filename.lower().endswith(".pdf"):
            return

        try:
            progreso_msg = await message.channel.send("⏳ Subiendo archivo...")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf_path = tmp.name
                await archivo.save(tmp)

            await progreso_msg.edit(content="📤 Subiendo archivo a gofile.io...")
            gofile_url = await subir_a_gofile(pdf_path)

            await progreso_msg.edit(content="📄 Procesando PDF...")
            user_id = str(message.author.id)

            async def registrar_progreso(porcentaje):
                barra = generar_barra_progreso(porcentaje)
                await progreso_msg.edit(content=f"✅ Progreso: {barra}")

            contactos = await extraer_contactos_desde_pdf(
                pdf_path,
                user_id,
                progreso_callback=registrar_progreso
            )

            await progreso_msg.edit(content="📦 Exportando a CSV...")
            ruta_csv = exportar_contactos_csv(archivo.filename, user_id, contactos)

            await progreso_msg.edit(content="📤 Subiendo CSV a gofile.io...")
            url_csv = await subir_a_gofile(ruta_csv)

            embed = discord.Embed(title="✅ PDF procesado con éxito", color=0x2ecc71)
            embed.add_field(name="📄 Archivo original", value=archivo.filename, inline=False)
            embed.add_field(name="👥 Contactos extraídos", value=f"{len(contactos):,}", inline=True)
            embed.add_field(name="⬇️ Descargar CSV", value=url_csv, inline=False)
            embed.set_footer(text="Gracias por utilizar VXbot | Servicio profesional ✨")

            await progreso_msg.edit(content="", embed=embed)
            custom_log(self.bot, "PDF_LISTENER", "INFO", f"✅ PDF cargado desde mensaje procesado correctamente.")

            limpiar_canal_despues(self.bot, message.channel)

        except Exception as e:
            await progreso_msg.edit(content=f"❌ Error al procesar PDF: {e}")
            custom_log(self.bot, "PDF_LISTENER", "ERROR", f"❌ Error al procesar PDF desde mensaje: {e}")

async def setup(bot):
    await bot.add_cog(PDFListener(bot))
