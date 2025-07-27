# comandos/exportar_csv.py
import discord
from discord import app_commands
from discord.ext import commands
import os
from utils.export_csv import exportar_contactos_csv
from utils.logger import custom_log

class ExportarCSV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="exportar_csv", description="Exporta un archivo CSV desde un PDF previamente procesado")
    @app_commands.describe(nombre_pdf="Nombre exacto del PDF procesado, incluyendo .pdf")
    async def exportar_csv(self, interaction: discord.Interaction, nombre_pdf: str):
        await interaction.response.defer(thinking=True)

        try:
            ruta_csv = exportar_contactos_csv(nombre_pdf)
            await interaction.followup.send(
                content=f"✅ Aquí está el archivo CSV generado para `{nombre_pdf}`:",
                file=discord.File(ruta_csv, filename=f"contactos_{nombre_pdf.replace('.pdf', '')}.csv")
            )
            custom_log(f"📤 CSV exportado: {nombre_pdf}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error al exportar CSV: {e}")
            custom_log(f"❌ Error al exportar CSV: {e}")

async def setup(bot):
    await bot.add_cog(ExportarCSV(bot))
