# comandos/validar_link_pdf.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os

CANAL_IMPORTAR_PDF = os.getenv("CANAL_IMPORTAR_PDF")

class ValidarLinkPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="validar_link_pdf", description="Valida si un enlace apunta a un archivo PDF real")
    @app_commands.describe(link="URL directa del archivo PDF")
    async def validar_link_pdf(self, interaction: discord.Interaction, link: str):
        if str(interaction.channel_id) != CANAL_IMPORTAR_PDF:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal autorizado.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link) as resp:
                    status = resp.status
                    content_type = resp.headers.get("Content-Type", "N/A")

                    if status != 200:
                        await interaction.followup.send(f"❌ Código HTTP {status}. No se pudo acceder al enlace.")
                        return

                    if "pdf" not in content_type.lower():
                        await interaction.followup.send(f"⚠️ El archivo no parece ser un PDF. Tipo detectado: `{content_type}`")
                        return

            await interaction.followup.send(f"✅ El enlace es válido y apunta a un PDF (`{content_type}`)")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al validar el enlace: {e}")

async def setup(bot):
    await bot.add_cog(ValidarLinkPDF(bot))
