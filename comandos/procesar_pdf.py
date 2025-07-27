# comandos/procesar_pdf.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import tempfile
import time
import fitz
from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.logger import custom_log

CANAL_IMPORTAR_PDF = os.getenv("CANAL_IMPORTAR_PDF")

class ProcesarPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="procesar_pdf", description="Procesa un archivo PDF cargado directamente en Discord")
    @app_commands.describe(archivo="Archivo PDF con los contactos")
    async def procesar_pdf(self, interaction: discord.Interaction, archivo: discord.Attachment):
        if str(interaction.channel_id) != CANAL_IMPORTAR_PDF:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal autorizado.", ephemeral=True)
            return

        if not archivo.filename.endswith(".pdf"):
            await interaction.response.send_message("❌ Solo se permiten archivos PDF.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        ruta_local = os.path.join(tempfile.gettempdir(), archivo.filename)
        await archivo.save(ruta_local)

        try:
            await interaction.followup.send(f"⏳ Procesando archivo: `{archivo.filename}`... Esto puede tardar varios minutos dependiendo del tamaño.")

            doc = fitz.open(ruta_local)
            total_paginas = len(doc)
            tiempo_inicio = time.time()
            fotos_detectadas = 0

            async def registrar_progreso(paginas, total, progreso, faltan):
                nonlocal fotos_detectadas
                try:
                    pagina = doc[paginas - 1]
                    fotos_detectadas += len(pagina.get_images(full=True))
                except:
                    pass

                bloques = 10
                llenos = int((progreso / 100) * bloques)
                vacios = bloques - llenos
                barra = "█" * llenos + "░" * vacios

                msg = f"📊 Progreso: [{barra}] {progreso}% | Página {paginas}/{total} | ⏳ Faltan: {faltan} seg."
                await interaction.followup.send(msg)
                custom_log("INFO", msg)

            contactos = extraer_contactos_desde_pdf(
                ruta_local,
                registrar_progreso=registrar_progreso
            )

            tiempo_total = int(time.time() - tiempo_inicio)
            resumen = (
                f"✅ Se procesaron **{len(contactos)} contactos** desde `{archivo.filename}`\n"
                f"📄 Total de páginas: {total_paginas}\n"
                f"🖼️ Fotos detectadas: {fotos_detectadas}\n"
                f"⏱️ Tiempo total: {tiempo_total} segundos"
            )
            await interaction.followup.send(resumen)
            custom_log("INFO", resumen)

        except Exception as e:
            await interaction.followup.send(f"❌ Error al procesar el PDF: {e}")
            custom_log("ERROR", f"❌ Error al procesar PDF: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDF(bot))
