import discord
from discord import app_commands
from discord.ext import commands
import os
import redis.asyncio as redis
from mensajes.comandos_texto import generar_embed_estado
from config import CANAL_COMANDOS

r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

class EstadoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema.")
    async def estado(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS:
            return await interaction.response.send_message("Este comando solo puede usarse en el canal de comandos.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        user_id = str(interaction.user.id)
        data = await r.hgetall(f"faltas:{user_id}")

        embed = generar_embed_estado(interaction.user, data)

        # Respuesta en canal (temporal)
        await interaction.followup.send(embed=embed, ephemeral=False, delete_after=600)

        # Enviar por DM también
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            print(f"❌ No se pudo enviar DM a {interaction.user}")

async def setup(bot):
    await bot.add_cog(EstadoCommand(bot))
