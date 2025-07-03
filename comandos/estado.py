import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ID, CANAL_COMANDOS_ID
from mensajes.comandos_texto import generar_embed_estado

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Consulta tu estado y tus faltas.")
    async def estado(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal 💻comandos.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        embed = await generar_embed_estado(interaction.user)

        # Respuesta en canal
        canal_msg = await interaction.followup.send(embed=embed, delete_after=600)

        # Respuesta por DM
        try:
            await interaction.user.send(embed=embed)
        except:
            print(f"❌ No se pudo enviar el DM a {interaction.user.name}.")

async def setup(bot):
    await bot.add_cog(Estado(bot))
