# comandos/procesar_pdf.py (finaliza con embed profesional)
import discord
from discord import app_commands
from discord.ext import commands
import os
import tempfile
import time
import fitz
from utils.pdf_parser import extraer_contactos_desde_pdf, extraer_datos_genericos_desde_pdf
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
            canal = interaction.channel
            progreso_msg = await canal.send(f"⏳ Procesando archivo: `{archivo.filename}`... Esto puede tardar varios minutos dependiendo del tamaño.")
            doc = fitz.open(ruta_local)
            total_paginas = len(doc)
            tiempo_inicio = time.time()
            fotos_detectadas = 0

            def formato_tiempo(segundos):
                if segundos >= 3600:
                    return f"{segundos // 3600}h {(segundos % 3600) // 60}m"
                elif segundos >= 60:
                    return f"{segundos // 60}m {segundos % 60}s"
                else:
                    return f"{segundos}s"

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
                estado = "✅" if progreso > 0 else "❌"
                tiempo_legible = formato_tiempo(faltan)
                msg = f"{estado} Progreso: [{barra}] {progreso}% | Página {paginas}/{total} | ⏳ Faltan: {tiempo_legible}"
                try:
                    await progreso_msg.edit(content=msg)
                except:
                    await canal.send(msg)

                custom_log(self.bot, "PROCESAR_PDF", "INFO", msg)

            contactos = await extraer_contactos_desde_pdf(
                ruta_local,
                registrar_progreso=registrar_progreso,
                clave_usuario=str(interaction.user.id)
            )

            tiempo_total = int(time.time() - tiempo_inicio)
            tiempo_legible = formato_tiempo(tiempo_total)

            if contactos and len(contactos) > 0:
                embed = discord.Embed(title="✅ PDF procesado correctamente", color=0x2ecc71)
                embed.add_field(name="Archivo", value=archivo.filename, inline=False)
                embed.add_field(name="Contactos", value=f"{len(contactos)} detectados", inline=True)
                embed.add_field(name="Páginas", value=f"{total_paginas}", inline=True)
                embed.add_field(name="Fotos", value=f"{fotos_detectadas}", inline=True)
                embed.add_field(name="Duración", value=tiempo_legible, inline=True)
                embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                await progreso_msg.edit(content=None, embed=embed)
                custom_log(self.bot, "PROCESAR_PDF", "INFO", f"✅ {len(contactos)} contactos detectados en {archivo.filename}")
            else:
                await progreso_msg.edit(content=f"⚠️ No se encontraron contactos estructurados. Intentando modo genérico...")
                genericos = await extraer_datos_genericos_desde_pdf(ruta_local, clave_usuario=str(interaction.user.id))
                if genericos:
                    embed = discord.Embed(title="✅ Datos genéricos extraídos", color=0xf1c40f)
                    embed.add_field(name="Archivo", value=archivo.filename, inline=False)
                    embed.add_field(name="Registros encontrados", value=str(len(genericos)), inline=True)
                    embed.add_field(name="Páginas analizadas", value=str(total_paginas), inline=True)
                    embed.add_field(name="Duración", value=tiempo_legible, inline=True)
                    embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                    await progreso_msg.edit(content=None, embed=embed)
                    custom_log(self.bot, "PROCESAR_PDF", "INFO", f"✅ {len(genericos)} registros genéricos extraídos de {archivo.filename}")
                else:
                    await progreso_msg.edit(content="❌ No se encontraron datos útiles en el PDF.")
                    custom_log(self.bot, "PROCESAR_PDF", "WARNING", f"PDF sin datos extraíbles: {archivo.filename}")
        except Exception as e:
            await canal.send(f"❌ Error al procesar el PDF: {e}")
            custom_log(self.bot, "PROCESAR_PDF", "ERROR", f"❌ Error al procesar PDF: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDF(bot))
