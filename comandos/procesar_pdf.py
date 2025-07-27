# comandos/procesar_pdf_url.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import tempfile
import time
import fitz
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
            await interaction.followup.send(f"⏳ Procesando archivo: `{nombre_pdf}` desde enlace externo... Esto puede tardar varios minutos dependiendo del tamaño.")

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

            doc = fitz.open(ruta_local)
            total_paginas = len(doc)
            tiempo_inicio = time.time()
            fotos_detectadas = 0

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

                msg = f"📊 Progreso: [{barra}] {progreso}% | Página {paginas}/{total} | ⏳ Faltan: {faltan} seg."
                await interaction.followup.send(msg)
                log("INFO", msg)

            contactos = await extraer_contactos_desde_pdf(
                ruta_local,
                registrar_progreso=registrar_progreso
            )

            tiempo_total = int(time.time() - tiempo_inicio)
            resumen = (
                f"✅ Se procesaron **{len(contactos)} contactos** desde `{nombre_pdf}`\n"
                f"📄 Total de páginas: {total_paginas}\n"
                f"🖼️ Fotos detectadas: {fotos_detectadas}\n"
                f"⏱️ Tiempo total: {tiempo_total} segundos"
            )
            await interaction.followup.send(resumen)
            log("INFO", resumen)

        except Exception as e:
            await interaction.followup.send(f"❌ Error al procesar PDF: {e}")
            log("ERROR", f"❌ Excepción durante procesamiento PDF desde URL: {e}")

async def setup(bot):
    await bot.add_cog(ProcesarPDFUrl(bot))
