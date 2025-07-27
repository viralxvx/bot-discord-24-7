# comandos/exportar_csv.py (validado, con URL dinámica y protección contra respuestas HTML grandes)
import discord
from discord import app_commands
from discord.ext import commands
import os
import csv
import requests
from utils.export_csv import exportar_contactos_csv
from utils.logger import custom_log

HOSTGATOR_UPLOAD_URL = os.getenv("HOSTGATOR_UPLOAD_URL")

class ExportarCSV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="exportar_csv", description="Exporta un archivo CSV desde un PDF previamente procesado")
    @app_commands.describe(nombre_pdf="Nombre exacto del PDF procesado, incluyendo .pdf")
    async def exportar_csv(self, interaction: discord.Interaction, nombre_pdf: str):
        await interaction.response.defer(thinking=True)

        user_id = str(interaction.user.id)

        try:
            ruta_csv = exportar_contactos_csv(nombre_pdf, user_id)

            # Verificar si el archivo CSV tiene al menos una fila de datos además del encabezado
            with open(ruta_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                filas = list(reader)
                if len(filas) <= 1:
                    await interaction.followup.send("⚠️ El archivo CSV está vacío. No hay contactos para exportar.")
                    return

            tamano_mb = os.path.getsize(ruta_csv) / (1024 * 1024)
            nombre_remoto = f"contactos_{user_id}_{nombre_pdf.replace('.pdf','')}.csv"

            if tamano_mb > 7.8:
                with open(ruta_csv, "rb") as f:
                    files = {"file": (nombre_remoto, f)}
                    headers = {"Authorization": f"Bearer {os.getenv('HOSTGATOR_TOKEN')}"}
                    response = requests.post(HOSTGATOR_UPLOAD_URL, files=files, headers=headers)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        url = data.get("url", "")
                    except Exception:
                        raise Exception("La respuesta del servidor no es JSON válido")

                    embed = discord.Embed(title="📤 CSV exportado por API", color=0xf39c12)
                    embed.add_field(name="Archivo", value=nombre_remoto, inline=False)
                    embed.add_field(name="Tamaño", value=f"{tamano_mb:.2f} MB", inline=True)
                    embed.add_field(name="Descarga directa", value=url, inline=False)
                    embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                    await interaction.followup.send(embed=embed)
                    custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV subido vía API: {url}")
                else:
                    content_type = response.headers.get("Content-Type", "")
                    if "html" in content_type.lower():
                        raise Exception(f"❌ Error {response.status_code}: respuesta no válida (HTML)")
                    raise Exception(f"API respondió con error {response.status_code}: {response.text[:500]}")

            else:
                embed = discord.Embed(title="📤 CSV generado con éxito", color=0x3498db)
                embed.add_field(name="Archivo procesado", value=nombre_pdf, inline=False)
                embed.add_field(name="Usuario", value=interaction.user.display_name, inline=True)
                embed.set_footer(text="Usa este archivo para importarlo en tu sistema o herramienta de listas.")

                await interaction.followup.send(
                    content=None,
                    file=discord.File(ruta_csv, filename=f"contactos_{nombre_pdf.replace('.pdf', '')}.csv"),
                    embed=embed
                )
                custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV exportado directo desde Discord: {nombre_pdf}")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al exportar CSV: {str(e)[:1800]}")
            custom_log(self.bot, "EXPORTAR_CSV", "ERROR", f"❌ Error al exportar CSV: {e}")

async def setup(bot):
    await bot.add_cog(ExportarCSV(bot))
# comandos/exportar_csv.py (valida que el CSV no esté vacío antes de exportar)
import discord
from discord import app_commands
from discord.ext import commands
import os
import csv
import requests
from utils.export_csv import exportar_contactos_csv
from utils.logger import custom_log

HOSTGATOR_UPLOAD_URL = os.getenv("HOSTGATOR_UPLOAD_URL")

class ExportarCSV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="exportar_csv", description="Exporta un archivo CSV desde un PDF previamente procesado")
    @app_commands.describe(nombre_pdf="Nombre exacto del PDF procesado, incluyendo .pdf")
    async def exportar_csv(self, interaction: discord.Interaction, nombre_pdf: str):
        await interaction.response.defer(thinking=True)

        user_id = str(interaction.user.id)

        try:
            ruta_csv = exportar_contactos_csv(nombre_pdf, user_id)

            # Verificar si el archivo CSV tiene al menos una fila de datos además del encabezado
            with open(ruta_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                filas = list(reader)
                if len(filas) <= 1:
                    await interaction.followup.send("⚠️ El archivo CSV está vacío. No hay contactos para exportar.")
                    return

            tamano_mb = os.path.getsize(ruta_csv) / (1024 * 1024)
            nombre_remoto = f"contactos_{user_id}_{nombre_pdf.replace('.pdf','')}.csv"

            if tamano_mb > 7.8:
                with open(ruta_csv, "rb") as f:
                    files = {"file": (nombre_remoto, f)}
                    headers = {"Authorization": f"Bearer {os.getenv('HOSTGATOR_TOKEN')}"}
                    response = requests.post("https://innovaguard.shop/api/upload_csv.php", files=files, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    url = data.get("url", "")
                    embed = discord.Embed(title="📤 CSV exportado por API", color=0xf39c12)
                    embed.add_field(name="Archivo", value=nombre_remoto, inline=False)
                    embed.add_field(name="Tamaño", value=f"{tamano_mb:.2f} MB", inline=True)
                    embed.add_field(name="Descarga directa", value=url, inline=False)
                    embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                    await interaction.followup.send(embed=embed)
                    custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV subido vía API: {url}")
                else:
                    raise Exception(f"API respondió con error {response.status_code}: {response.text}")

            else:
                embed = discord.Embed(title="📤 CSV generado con éxito", color=0x3498db)
                embed.add_field(name="Archivo procesado", value=nombre_pdf, inline=False)
                embed.add_field(name="Usuario", value=interaction.user.display_name, inline=True)
                embed.set_footer(text="Usa este archivo para importarlo en tu sistema o herramienta de listas.")

                await interaction.followup.send(
                    content=None,
                    file=discord.File(ruta_csv, filename=f"contactos_{nombre_pdf.replace('.pdf', '')}.csv"),
                    embed=embed
                )
                custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV exportado directo desde Discord: {nombre_pdf}")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al exportar CSV: {e}")
            custom_log(self.bot, "EXPORTAR_CSV", "ERROR", f"❌ Error al exportar CSV: {e}")

async def setup(bot):
    await bot.add_cog(ExportarCSV(bot))
