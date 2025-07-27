# comandos/procesar_pdf_url.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import tempfile
from utils.pdf_parser import extraer_contactos_desde_pdf

try:
    from utils.logger import custom_log
    usar_log = True
except:
    usar_log = False

def log(level, message):
    if usar_log:
        try:
            custom_log(level, message)
        except Exception as e:
            print(f"[{level}] {message} (LOG ERROR: {e})")
    else:
        print(f"[{level}] {message}")

CANAL_IMPORTAR_PDF = os.getenv("CANAL_IMPORTAR_PDF")

class ProcesarPDFUrl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="procesar_pdf_url", description="Procesa un PDF desde una URL directa (Dropbox, Drive, etc.)")
    @app_commands.describe(link="URL directa del PDF")
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
                    status = resp.status
                    content_type = resp.headers.get("Content-Type", "").lower()

                    if status != 200:
                        await interaction.followup.send(f"❌ No se pudo descargar el archivo. Código HTTP {status}.")
                        log("ERROR", f"❌ Código {status} al intentar acceder al link: {link}")
                        return

                    if any(x in content_type for x in ["html", "text"]):
                        await interaction.followup.send(f"⚠️ El archivo descargado **no es un PDF válido**. Tipo detectado: `{content_type}`")
                        log("ERROR", f"❌ Contenido HTML descargado desde: {link} ({content_type})")
                        return

                    with open(ruta_local, "wb") as f:
                        f.write(await resp.read())

            contactos = extraer_contactos_desde_pdf(ruta_local)
            await interaction.followup.send(f"✅ Se procesaron **{len(contactos)} contactos** desde `{nombre_pdf}`.")
            log("INFO", f"✅ PDF procesado desde URL: {nombre_pdf} ({len(contactos)} contactos)")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al procesar PDF: {e}")
            log("ERROR", f"❌ Excepción durante procesamiento PDF desde URL: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDFUrl(bot))
