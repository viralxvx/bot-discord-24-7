# comandos/exportar_csv.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import csv
import requests
from utils.export_csv import exportar_contactos_csv
from utils.logger import custom_log

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

            # Verifica si el archivo tiene datos
            with open(ruta_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                filas = list(reader)
                if len(filas) <= 1:
                    await interaction.followup.send("⚠️ El archivo CSV está vacío. No hay contactos para exportar.")
                    return

            tamano_mb = os.path.getsize(ruta_csv) / (1024 * 1024)
            nombre_csv = f"contactos_{user_id}_{nombre_pdf.replace('.pdf', '')}.csv"

            # 🔄 Subir a gofile.io si el archivo es muy grande
            if tamano_mb > 7.8:
                with open(ruta_csv, "rb") as f:
                    files = {"file": (nombre_csv, f)}
                    response = requests.post("https://store1.gofile.io/uploadFile", files=files)

                if response.status_code == 200 and response.json().get("status") == "ok":
                    url = response.json()["data"]["downloadPage"]
                    embed = discord.Embed(title="📤 CSV exportado a Gofile", color=0xf39c12)
                    embed.add_field(name="Archivo", value=nombre_csv, inline=False)
                    embed.add_field(name="Tamaño", value=f"{tamano_mb:.2f} MB", inline=True)
                    embed.add_field(name="Descarga directa", value=url, inline=False)
                    embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                    await interaction.followup.send(embed=embed)
                    custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV subido a gofile.io: {url}")
                else:
                    raise Exception("Error al subir el archivo a gofile.io")

            else:
                embed = discord.Embed(title="📤 CSV generado con éxito", color=0x3498db)
                embed.add_field(name="Archivo procesado", value=nombre_pdf, inline=False)
                embed.add_field(name="Usuario", value=interaction.user.display_name, inline=True)
                embed.set_footer(text="Usa este archivo para importarlo en tu sistema o herramienta de listas.")
                await interaction.followup.send(
                    file=discord.File(ruta_csv, filename=nombre_csv),
                    embed=embed
                )
                custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV exportado directo por Discord: {nombre_pdf}")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al exportar CSV: {e}")
            custom_log(self.bot, "EXPORTAR_CSV", "ERROR", f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(ExportarCSV(bot))
