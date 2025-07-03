import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ID, CANAL_COMANDOS_ID
from mensajes.comandos_texto import generar_embed_estadisticas

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estadisticas", description="Estadísticas generales del sistema de faltas.")
    async def estadisticas(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal autorizado.",
                ephemeral=True
            )
            return

        if interaction.user.id != int(ADMIN_ID) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "⛔ Solo administradores pueden usar este comando.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)
        embed = await generar_embed_estadisticas(self.bot)

        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send("⚠️ No pude enviarte un DM. Verifica tu configuración de privacidad.")
            return

        msg = await interaction.followup.send("📊 Estadísticas enviadas por DM.", ephemeral=False)
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(minutes=10))
        await msg.delete()

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
