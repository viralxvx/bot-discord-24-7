# comandos/procesar_pdf.py
import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import aiohttp
import tempfile
from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.logger import custom_log
from utils.export_csv import exportar_contactos_csv
from utils.gofile import subir_a_gofile
from utils.discord_tools import generar_barra_progreso, limpiar_canal_despues

class ProcesarPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="procesar_pdf", description="Convierte un PDF a CSV extrayendo contactos")
    async def procesar_pdf(self, interaction: discord.Interaction, archivo: discord.Attachment):
        await interaction.response.defer(thinking=True)

        user_id = str(interaction.user.id)
        canal = interaction.channel

        if not archivo.filename.lower().endswith(".pdf"):
            await interaction.followup.send("❌ El archivo debe ser un PDF válido.")
            return

        progreso_msg = await canal.send("⏳ Subiendo archivo...")

        try:
            # 1. Descargar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf_path = tmp.name
                await archivo.save(tmp)

            await progreso_msg.edit(content="📤 Subiendo archivo a gofile.io...")
            gofile_url = await subir_a_gofile(pdf_path)

            await progreso_msg.edit(content="📄 Procesando PDF...")
            contactos = await extraer_contactos_desde_pdf(
                pdf_path,
                user_id,
                progreso_callback=lambda p: self.actualizar_progreso(progreso_msg, p)
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
            custom_log(self.bot, "PROCESAR_PDF", "INFO", f"✅ PDF procesado y CSV exportado: {archivo.filename}")

            limpiar_canal_despues(self.bot, canal)

        except Exception as e:
            await progreso_msg.edit(content=f"❌ Error al procesar PDF: {e}")
            custom_log(self.bot, "PROCESAR_PDF", "ERROR", f"❌ Error al procesar PDF: {e}")

    async def actualizar_progreso(self, mensaje, porcentaje):
        barra = generar_barra_progreso(porcentaje)
        await mensaje.edit(content=f"[Activo] ✅ Progreso: {barra} {porcentaje}%")


async def setup(bot):
    await bot.add_cog(ProcesarPDF(bot))
