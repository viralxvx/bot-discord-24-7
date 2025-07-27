# comandos/procesar_pdf.py
import discord
from discord import app_commands
from discord.ext import commands
import os
from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.logger import custom_log

discord_allowed_channel = os.getenv("CANAL_IMPORTAR_PDF")

class ProcesarPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="procesar_pdf", description="Procesa un archivo PDF y extrae todos los contactos")
    @app_commands.describe(archivo="Archivo PDF con los contactos")
    async def procesar_pdf(self, interaction: discord.Interaction, archivo: discord.Attachment):
        if str(interaction.channel_id) != discord_allowed_channel:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal autorizado.", ephemeral=True)
            return

        if not archivo.filename.endswith(".pdf"):
            await interaction.response.send_message("❌ Solo se permiten archivos PDF.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        
        ruta_local = f"/tmp/{archivo.filename}"
        await archivo.save(ruta_local)

        try:
            contactos = extraer_contactos_desde_pdf(ruta_local)
            custom_log(f"✅ PDF procesado: {archivo.filename} ({len(contactos)} contactos extraídos)")
            await interaction.followup.send(f"✅ Listo. Se extrajeron **{len(contactos)} contactos** desde `{archivo.filename}`.")
        except Exception as e:
            custom_log(f"❌ Error procesando PDF: {e}")
            await interaction.followup.send(f"❌ Error al procesar el PDF: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDF(bot))
