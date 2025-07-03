import discord
from discord import app_commands
from discord.ext import commands
from config import CANAL_COMANDOS_ID
from mensajes.comandos_texto import generar_embed_estado

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema de faltas.")
    async def estado(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal autorizado.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)
        embed = await generar_embed_estado(interaction.user.id, self.bot)

        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send("⚠️ No pude enviarte un DM. Verifica tu configuración de privacidad.")
            return

        msg = await interaction.followup.send("📬 ¡Revisa tu DM! Te envié tu estado.", ephemeral=False)
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(minutes=10))
        await msg.delete()

async def setup(bot):
    await bot.add_cog(Estado(bot))
