import discord
from discord import app_commands
from discord.ext import commands
import os
import redis.asyncio as redis
from mensajes.comandos_texto import generar_embed_estadisticas
from config import ADMIN_ID, CANAL_COMANDOS

r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

class EstadisticasCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estadisticas", description="Consulta estadísticas del sistema (solo admins).")
    async def estadisticas(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS:
            return await interaction.response.send_message("Este comando solo puede usarse en el canal de comandos.", ephemeral=True)

        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("No tienes permisos para este comando.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        keys = await r.keys("faltas:*")
        total_miembros = len(keys)

        baneados = 0
        expulsados = 0
        for key in keys:
            data = await r.hgetall(key)
            if data.get("estado") == "baneado":
                baneados += 1
            elif data.get("estado") == "expulsado":
                expulsados += 1

        embed = generar_embed_estadisticas(total_miembros, baneados, expulsados)

        # Enviar en canal (temporal)
        await interaction.followup.send(embed=embed, ephemeral=False, delete_after=600)

        # Enviar por DM
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            print(f"❌ No se pudo enviar DM a {interaction.user}")

async def setup(bot):
    await bot.add_cog(EstadisticasCommand(bot))
