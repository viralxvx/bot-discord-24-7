# comandos/procesar_pdf.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import uuid
import asyncio
from utils.logger import custom_log
from utils.progreso import crear_barra_progreso
from utils.discord_tools import obtener_canal_por_nombre
from utils.pdf_tools import convertir_pdf_a_texto
from utils.pdf_parser import extraer_datos_genericos_desde_pdf

CANAL_IMPORTAR_PDF = "📥importar-pdf"
TEMP_FOLDER = "temp"

class ProcesarPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="procesar_pdf", description="Procesa un PDF que hayas subido en el canal 📥importar-pdf.")
    async def procesar_pdf(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        canal_permitido = obtener_canal_por_nombre(self.bot, CANAL_IMPORTAR_PDF)
        if interaction.channel != canal_permitido:
            await interaction.followup.send(f"❌ Este comando solo puede usarse en {canal_permitido.mention}", ephemeral=True)
            return

        mensajes = [msg async for msg in interaction.channel.history(limit=20)]
        archivo_pdf = None

        for mensaje in mensajes:
            if mensaje.attachments:
                for adjunto in mensaje.attachments:
                    if adjunto.filename.lower().endswith(".pdf"):
                        archivo_pdf = adjunto
                        break
            if archivo_pdf:
                break

        if not archivo_pdf:
            await interaction.followup.send("❌ No se encontró ningún archivo PDF en los últimos mensajes.", ephemeral=True)
            return

        os.makedirs(TEMP_FOLDER, exist_ok=True)

        archivo_id = str(uuid.uuid4())
        ruta_pdf = os.path.join(TEMP_FOLDER, f"{archivo_id}.pdf")

        try:
            await archivo_pdf.save(ruta_pdf)
        except Exception as e:
            custom_log("ERROR", f"Error guardando PDF: {e}")
            await interaction.followup.send("❌ Error al guardar el PDF.", ephemeral=True)
            return

        try:
            rutas_txt = await convertir_pdf_a_texto(ruta_pdf, archivo_id, registrar_progreso=True)
            contactos = await extraer_datos_genericos_desde_pdf(rutas_txt, archivo_id, user_id=interaction.user.id, registrar_progreso=True)

            total = len(contactos)
            mensaje_final = f"✅ PDF procesado: {total} contacto{'s' if total != 1 else ''} detectado{'s' if total != 1 else ''}."
            await interaction.followup.send(mensaje_final, ephemeral=True)

        except Exception as e:
            custom_log("ERROR", f"[Activo] Error procesando PDF: {e}: ERROR")
            await interaction.followup.send(f"❌ Error procesando PDF: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProcesarPDF(bot))
