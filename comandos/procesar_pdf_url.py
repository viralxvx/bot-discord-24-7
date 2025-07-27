# comandos/procesar_pdf_url.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
from utils.gofile import subir_a_gofile
from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.logger import custom_log
from utils.progreso import crear_barra_progreso
from utils.export_csv import exportar_contactos_csv
import asyncio

class ProcesarPDFUrl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="procesar_pdf_url", description="Procesa un PDF desde una URL y extrae contactos")
    @app_commands.describe(url="URL del archivo PDF")
    async def procesar_pdf_url(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer(thinking=True)
        user_id = str(interaction.user.id)

        # Crear mensaje de progreso inicial
        progreso_msg = await interaction.followup.send("🔄 Procesando archivo...")

        try:
            # Descargar el archivo PDF
            nombre_archivo = f"pdf_{user_id}.pdf"
            ruta_pdf = f"temp/{nombre_archivo}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise Exception("No se pudo descargar el archivo PDF")
                    with open(ruta_pdf, "wb") as f:
                        f.write(await resp.read())

            await progreso_msg.edit(content="✅ Archivo descargado. Iniciando extracción de datos...")

            async def registrar_progreso(pagina_actual, total_paginas):
                porcentaje = int((pagina_actual / total_paginas) * 100)
                barra = crear_barra_progreso(porcentaje)
                await progreso_msg.edit(content=f"[Activo] ✅ Progreso: {barra} {porcentaje}% | Página {pagina_actual}/{total_paginas}")

            contactos = await extraer_contactos_desde_pdf(ruta_pdf, user_id, registrar_progreso)

            if not contactos:
                await progreso_msg.edit(content="⚠️ No se encontraron contactos válidos en el PDF.")
                return

            # Exportar CSV
            ruta_csv = exportar_contactos_csv(nombre_archivo, user_id)
            await progreso_msg.edit(content=f"✅ Extracción completada. Subiendo CSV a gofile.io...")

            # Subir CSV a gofile.io
            url_descarga = await subir_a_gofile(ruta_csv)

            embed = discord.Embed(title="📄 PDF procesado exitosamente", color=0x2ecc71)
            embed.add_field(name="Total contactos", value=str(len(contactos)), inline=True)
            embed.add_field(name="Descargar CSV", value=f"[Haz clic aquí]({url_descarga})", inline=False)
            embed.set_footer(text="Gracias por usar VXbot | El canal será limpiado en 1 hora")

            await progreso_msg.edit(content=None, embed=embed)

            # Agendar limpieza del canal
            await asyncio.sleep(3600)
            await progreso_msg.delete()

        except Exception as e:
            await progreso_msg.edit(content=f"❌ Error al procesar PDF: {e}")
            custom_log(self.bot, "PROCESAR_PDF_URL", "ERROR", f"❌ Excepción durante procesamiento PDF desde URL: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDFUrl(bot))
