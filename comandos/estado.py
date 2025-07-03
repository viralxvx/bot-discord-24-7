import discord
from discord import app_commands
from discord.ext import commands
import os
import redis
import json
from comandos.mensajes import generar_embed_estado

CANAL_COMANDOS_ID = 1390164280959303831
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Consulta tu situación actual en el servidor.")
    async def estado(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            return  # Solo se ejecuta en el canal 💻comandos

        user_id = str(interaction.user.id)
        data = redis_client.get(f"faltas:{user_id}")
        info = json.loads(data) if data else {"faltas": 0, "estado": "Activo"}

        embed = generar_embed_estado(interaction.user, info)

        try:
            # Enviar al canal
            canal_msg = await interaction.response.send_message(embed=embed, ephemeral=False)
            # Enviar por DM
            await interaction.user.send(embed=embed)
        except Exception as e:
            print(f"❌ Error enviando embed: {e}")

async def setup(bot):
    await bot.add_cog(Estado(bot))
