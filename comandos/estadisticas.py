import discord
from discord import app_commands
from discord.ext import commands
from config import CANAL_COMANDOS_ID
from mensajes.comandos_texto import generar_embed_estadisticas

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estadisticas", description="Ver estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Este comando está reservado para administradores.", ephemeral=True)
                return

            if interaction.channel.id != CANAL_COMANDOS_ID:
                await interaction.response.send_message("❌ Este comando solo puede usarse en el canal 💻comandos.", ephemeral=True)
                return

            await interaction.response.defer()

            guild = interaction.guild
            total_miembros = len([m for m in guild.members if not m.bot])
            total_baneados = await guild.bans()
            total_baneados_count = len(total_baneados)

            # Por ahora no estamos guardando expulsados, se pone en 0
            total_expulsados = 0

            embed = await generar_embed_estadisticas(
                interaction.user,
                total_miembros,
                total_baneados_count,
                total_expulsados
            )

            # Responder en canal de comandos (duración: 10 minutos)
            await interaction.followup.send(embed=embed, delete_after=600)

            # Responder también por DM
            try:
                await interaction.user.send(embed=embed)
            except discord.Forbidden:
                print(f"⚠️ No se pudo enviar DM a {interaction.user.display_name}")

            print(f"📊 [LOG] Usuario ejecutó /estadisticas: {interaction.user.display_name} ({interaction.user.id})")

        except Exception as e:
            print(f"❌ Error en /estadisticas: {e}")
            await interaction.followup.send("❌ Hubo un error al procesar las estadísticas. Contacta a un moderador.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
