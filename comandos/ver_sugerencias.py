# comandos/ver_sugerencias.py

import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_COMANDOS_ID

class VerSugerencias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ver_sugerencias",
        description="Ver sugerencias enviadas por los usuarios (solo admins)"
    )
    async def ver_sugerencias(self, interaction: discord.Interaction):
        # Solo permitido en canal de comandos
        if interaction.channel_id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal 💻comandos.",
                ephemeral=True
            )
            return

        # Solo admins o moderadores
        if not (
            interaction.user.guild_permissions.administrator or 
            interaction.user.guild_permissions.manage_guild
        ):
            await interaction.response.send_message(
                "❌ No tienes permisos para usar este comando.",
                ephemeral=True
            )
            return

        # Respuesta de prueba
        await interaction.response.send_message(
            "✅ Comando `/ver_sugerencias` registrado correctamente. (versión mínima)",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(VerSugerencias(bot))
