# comandos/procesar_pdf.py (todo en uno: PDF grande ➜ subir, procesar, exportar, entregar)
import discord
from discord import app_commands
from discord.ext import commands
import os
import tempfile
import time
import requests
import fitz
from utils.pdf_parser import extraer_contactos_desde_pdf, extraer_datos_genericos_desde_pdf
from utils.export_csv import exportar_contactos_csv
from utils.logger import custom_log
import csv

CANAL_IMPORTAR_PDF = os.getenv("CANAL_IMPORTAR_PDF")
HOSTGATOR_UPLOAD_URL = "https://innovaguard.shop/api/vxpdf.php"

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
        tamano_pdf_mb = os.path.getsize(ruta_local) / (1024 * 1024)

        canal = interaction.channel
        progreso_msg = await canal.send(f"⏳ Procesando archivo: `{archivo.filename}`...")

        if tamano_pdf_mb > 8:
            try:
                with open(ruta_local, "rb") as f:
                    files = {"file": (archivo.filename, f)}
                    headers = {"Authorization": f"Bearer {os.getenv('HOSTGATOR_TOKEN')}"}
                    response = requests.post(HOSTGATOR_UPLOAD_URL, files=files, headers=headers)
                if response.status_code == 200:
                    url_pdf = response.json().get("url", "")
                    await progreso_msg.edit(content=f"📤 PDF subido al hosting: {url_pdf}\nProcesando...")
                else:
                    raise Exception(f"Host respondió {response.status_code}: {response.text}")
            except Exception as e:
                await canal.send(f"❌ Error al subir PDF grande: {e}")
                return

        try:
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
            user_id = str(interaction.user.id)

            if not contactos or len(contactos) == 0:
                await progreso_msg.edit(content=f"⚠️ No se encontraron contactos estructurados. Intentando modo genérico...")
                contactos = await extraer_datos_genericos_desde_pdf(ruta_local, clave_usuario=user_id)

            # Exportar CSV
            ruta_csv = exportar_contactos_csv(archivo.filename, user_id)
            with open(ruta_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                filas = list(reader)
                if len(filas) <= 1:
                    await progreso_msg.edit(content="⚠️ El CSV está vacío. No se encontraron datos útiles.")
                    return

            tamano_csv = os.path.getsize(ruta_csv) / (1024 * 1024)
            nombre_csv = f"contactos_{user_id}_{archivo.filename.replace('.pdf','')}.csv"

            if tamano_csv > 7.8:
                with open(ruta_csv, "rb") as f:
                    files = {"file": (nombre_csv, f)}
                    headers = {"Authorization": f"Bearer {os.getenv('HOSTGATOR_TOKEN')}"}
                    response = requests.post(HOSTGATOR_UPLOAD_URL, files=files, headers=headers)
                if response.status_code == 200:
                    url = response.json().get("url", "")
                    embed = discord.Embed(title="📤 PDF procesado y CSV subido", color=0x2ecc71)
                    embed.add_field(name="Archivo PDF", value=archivo.filename, inline=False)
                    embed.add_field(name="Contactos/Registros", value=str(len(contactos)), inline=True)
                    embed.add_field(name="Duración", value=tiempo_legible, inline=True)
                    embed.add_field(name="Descargar CSV", value=url, inline=False)
                    embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                    await progreso_msg.edit(content=None, embed=embed)
                    custom_log(self.bot, "PROCESAR_PDF", "INFO", f"CSV grande subido: {url}")
                else:
                    raise Exception(f"Error al subir CSV: {response.status_code}: {response.text}")
            else:
                embed = discord.Embed(title="✅ PDF procesado y CSV generado", color=0x3498db)
                embed.add_field(name="Archivo PDF", value=archivo.filename, inline=False)
                embed.add_field(name="Contactos/Registros", value=str(len(contactos)), inline=True)
                embed.add_field(name="Duración", value=tiempo_legible, inline=True)
                embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                await progreso_msg.edit(content=None, embed=embed, file=discord.File(ruta_csv, filename=nombre_csv))

        except Exception as e:
            await canal.send(f"❌ Error al procesar PDF: {e}")
            custom_log(self.bot, "PROCESAR_PDF", "ERROR", f"❌ Error al procesar PDF: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDF(bot))
