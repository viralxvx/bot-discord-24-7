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

            # Verifica si el archivo tiene contenido útil
            with open(ruta_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                filas = list(reader)
                if len(filas) <= 1:
                    await interaction.followup.send("⚠️ El archivo CSV está vacío. No hay contactos para exportar.")
                    return

            tamano_mb = os.path.getsize(ruta_csv) / (1024 * 1024)

            if tamano_mb > 7.8:
                with open(ruta_csv, "rb") as f:
                    nombre_remoto = f"contactos_{user_id}_{nombre_pdf.replace('.pdf','')}.csv"
                    response = requests.put(
                        f"https://transfer.sh/{nombre_remoto}",
                        data=f,
                        headers={"Max-Downloads": "10", "Max-Days": "7"}
                    )

                if response.status_code == 200:
                    url = response.text.strip()
                    embed = discord.Embed(title="📤 CSV exportado con éxito", color=0x2ecc71)
                    embed.add_field(name="Archivo", value=nombre_remoto, inline=False)
                    embed.add_field(name="Tamaño", value=f"{tamano_mb:.2f} MB", inline=True)
                    embed.add_field(name="Descarga directa", value=url, inline=False)
                    embed.set_footer(text=f"Usuario: {interaction.user.display_name}")
                    await interaction.followup.send(embed=embed)
                    custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV subido a transfer.sh: {url}")
                else:
                    raise Exception(f"transfer.sh respondió con error {response.status_code}: {response.text}")

            else:
                # Si es pequeño, envía directo por Discord
                embed = discord.Embed(title="📤 CSV generado con éxito", color=0x3498db)
                embed.add_field(name="Archivo procesado", value=nombre_pdf, inline=False)
                embed.set_footer(text="Usa este archivo para importarlo en tu sistema o herramienta de listas.")

                await interaction.followup.send(
                    content=None,
                    file=discord.File(ruta_csv, filename=f"contactos_{nombre_pdf.replace('.pdf', '')}.csv"),
                    embed=embed
                )
                custom_log(self.bot, "EXPORTAR_CSV", "INFO", f"📤 CSV enviado desde Discord: {nombre_pdf}")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al exportar CSV: {e}")
            custom_log(self.bot, "EXPORTAR_CSV", "ERROR", f"❌ {e}")

async def setup(bot):
    await bot.add_cog(ExportarCSV(bot))
