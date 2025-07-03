import discord
from discord import app_commands
from discord.ext import commands
import os
import redis
import json
from comandos.mensajes import generar_embed_estadisticas

CANAL_COMANDOS_ID = 1390164280959303831
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estadísticas", description="Estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            return  # Solo se ejecuta en 💻comandos

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo los administradores pueden usar este comando.", ephemeral=True)
            return

        # Datos de Redis
        todos = redis_client.keys("faltas:*")
        total = len(todos)
        baneados = sum(1 for k in todos if json.loads(redis_client.get(k)).get("estado") == "Baneado")
        expulsados = sum(1 for k in todos if json.loads(redis_client.get(k)).get("estado") == "Expulsado")

        embed = generar_embed_estadisticas(total, baneados, expulsados)

        try:
            # Enviar al canal y por DM
            await interaction.response.send_message(embed=embed, ephemeral=False)
            await interaction.user.send(embed=embed)
        except Exception as e:
            print(f"❌ Error enviando estadísticas: {e}")

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
