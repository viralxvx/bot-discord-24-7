# comandos/exportar_csv.py

import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import csv
import aiofiles
import requests
from utils.export_csv import exportar_contactos_csv
from utils.logger import custom_log
from utils.gofile import subir_a_gofile
from utils.cleanup import agendar_eliminacion_mensaje

class ExportarCSV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="exportar_csv", description="Exporta un CSV del PDF procesado")
    @app_commands.describe(nombre_pdf="Nombre exacto del PDF procesado (incluyendo .pdf)")
    async def exportar_csv(self, interaction: discord.Interaction, nombre_pdf: str):
        await interaction.response.defer(thinking=True)

        user_id = str(interaction.user.id)
        progreso_msg = await interaction.followup.send("⏳ Preparando exportación...")

        try:
            ruta_csv = exportar_contactos_csv(nombre_pdf, user_id)
            tamano_mb = os.path.getsize(ruta_csv) / (1024 * 1024)

            # Validación del contenido útil
            with open(ruta_csv, newline='', encoding='utf-8') as f:
                filas = list(csv.reader(f))
                if len(filas) <= 1:
                    await progreso_msg.edit(content="⚠️ El archivo CSV está vacío. No hay datos válidos para exportar.")
                    return

            # Mensaje de progreso inicial
            await progreso_msg.edit(content="📤 Exportando CSV...\n[░░░░░░░░░░] 0%")

            if tamano_mb > 7.9:
                await progreso_msg.edit(content="📡 Subiendo CSV a gofile.io...\n[████░░░░░░] 50%")
                gofile_url = subir_a_gofile(ruta_csv)
                await progreso_msg.edit(content=f"""
✅ Exportación completada al 100%
[██████████] 100%

📎 Archivo listo para descargar:
{gofile_url}

Gracias por usar **VXbot**. Este mensaje se eliminará en 1 hora para mantener el canal limpio.
                """)
            else:
                await progreso_msg.edit(content="📦 CSV generado con éxito. Subiendo al canal...")
                await progreso_msg.edit(content=None, file=discord.File(ruta_csv, filename=os.path.basename(ruta_csv)))

            agendar_eliminacion_mensaje(progreso_msg)

            custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"✅ CSV exportado: {nombre_pdf} ({tamano_mb:.2f} MB)")

        except Exception as e:
            await progreso_msg.edit(content=f"❌ Error al exportar CSV: {e}")
            custom_log(self.bot, "EXPORTAR_CSV", "ERROR", f"❌ Error al exportar CSV: {e}")

async def setup(bot):
    await bot.add_cog(ExportarCSV(bot))
