# comandos/estado.py

import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import redis
import json
from comandos.mensajes import ERROR_DM
from datetime import datetime, timedelta

CANAL_COMANDOS = int(os.getenv("CANAL_COMANDOS"))
REDIS_URL = os.getenv("REDIS_URL")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema de faltas.")
    async def estado(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse en el canal autorizado.", ephemeral=True
            )
            return

        user = interaction.user
        user_id = str(user.id)
        datos = r.get(f"faltas:{user_id}")
        datos_usuario = json.loads(datos) if datos else {}

        # Construimos embed
        embed = discord.Embed(
            title="📋 Estado del Usuario",
            description=f"Información para: {user.mention}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Faltas Totales", value=str(datos_usuario.get("total_faltas", 0)), inline=True)
        embed.add_field(name="Faltas Este Mes", value=str(datos_usuario.get("faltas_mes", 0)), inline=True)
        embed.add_field(name="Estado", value=datos_usuario.get("estado", "Activo"), inline=True)
        embed.add_field(name="Última Falta", value=datos_usuario.get("ultima_falta", "N/A"), inline=True)
        embed.set_footer(text="VXbot • Sistema de Faltas")

        # Enviar respuesta pública en el canal
        await interaction.response.send_message(embed=embed, delete_after=600)

        # Enviar por DM
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send(ERROR_DM, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estado(bot))
