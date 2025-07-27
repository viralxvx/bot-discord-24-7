# comandos/procesar_pdf_url.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import tempfile
from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.logger import custom_log

CANAL_IMPORTAR_PDF = os.getenv("CANAL_IMPORTAR_PDF")

class ProcesarPDFUrl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="procesar_pdf_url", description="Procesa un PDF desde una URL externa (Dropbox, Drive, etc.)")
    @app_commands.describe(link="URL directa al archivo PDF (asegúrate de que sea pública)")
    async def procesar_pdf_url(self, interaction: discord.Interaction, link: str):
        if str(interaction.channel_id) != CANAL_IMPORTAR_PDF:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal autorizado.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        nombre_pdf = link.split("/")[-1].split("?")[0] or "archivo.pdf"
        ruta_local = os.path.join(tempfile.gettempdir(), nombre_pdf)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link) as resp:
                    if resp.status != 200:
                        raise Exception(f"No se pudo descargar el archivo. Código {resp.status}")
                    with open(ruta_local, "wb") as f:
                        f.write(await resp.read())

            contactos = extraer_contactos_desde_pdf(ruta_local)
            await interaction.followup.send(f"✅ Se procesaron **{len(contactos)} contactos** desde el archivo `{nombre_pdf}`.")
            custom_log("INFO", f"PDF por URL procesado correctamente: {nombre_pdf} ({len(contactos)} contactos)")
        except Exception as e:
            await interaction.followup.send(f"❌ Error al procesar PDF desde URL: {e}")
            custom_log("ERROR", f"❌ Error al procesar PDF desde URL: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDFUrl(bot))
