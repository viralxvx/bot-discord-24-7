# comandos/estadisticas.py

import discord
from discord import app_commands
from discord.ext import commands
import os
import redis
import json
from comandos.mensajes import ERROR_DM

CANAL_COMANDOS = int(os.getenv("CANAL_COMANDOS"))
REDIS_URL = os.getenv("REDIS_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estadisticas", description="Estadísticas globales del sistema de faltas.")
    async def estadisticas(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS:
            await interaction.response.send_message("❌ Este comando solo está permitido en el canal autorizado.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator and interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("⛔ Este comando es exclusivo para administradores.", ephemeral=True)
            return

        total_miembros = 0
        total_baneados = 0
        total_expulsados = 0

        claves = r.keys("faltas:*")
        for clave in claves:
            datos = json.loads(r.get(clave))
            total_miembros += 1
            estado = datos.get("estado", "activo").lower()
            if estado == "baneado":
                total_baneados += 1
            elif estado == "expulsado":
                total_expulsados += 1

        embed = discord.Embed(
            title="📊 Estadísticas Globales",
            description="Resumen del sistema de faltas",
            color=discord.Color.purple()
        )
        embed.add_field(name="Miembros Registrados", value=str(total_miembros), inline=True)
        embed.add_field(name="Baneados", value=str(total_baneados), inline=True)
        embed.add_field(name="Expulsados", value=str(total_expulsados), inline=True)
        embed.set_footer(text="VXbot • Sistema de Faltas")

        # Enviar en canal
        await interaction.response.send_message(embed=embed, delete_after=600)

        # Enviar por DM
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send(ERROR_DM, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
