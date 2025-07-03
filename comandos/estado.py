import discord
from discord import app_commands
from discord.ext import commands
from redis.commands.json.path import Path
import redis
import os
import json

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema de faltas.")
    async def estado(self, interaction: discord.Interaction):
        user = interaction.user
        user_id = str(user.id)
        guild_id = os.getenv("GUILD_ID")

        print(f"🧪 [LOG] Usuario ejecutó /estado: {user.name} ({user_id})")

        data = self.redis.hgetall(f"{guild_id}:faltas:{user_id}")

        total = data.get("total", "0")
        mes = data.get("mes", "0")
        estado = data.get("estado", "activo")

        embed = discord.Embed(
            title="📋 Tu Estado Actual",
            description=f"👤 Usuario: {user.mention}",
            color=discord.Color.orange()
        )
        embed.add_field(name="📅 Faltas del mes", value=mes, inline=True)
        embed.add_field(name="📊 Total de faltas", value=total, inline=True)
        embed.add_field(name="⚠️ Estado actual", value=estado.upper(), inline=False)
        embed.set_footer(text="Sistema automatizado de faltas VX")

        try:
            await user.send(embed=embed)
            await interaction.response.send_message("✅ Te envié tu estado por DM.", ephemeral=True)
        except Exception as e:
            print(f"❌ Error al enviar DM: {e}")
            await interaction.response.send_message("❌ No pude enviarte un mensaje privado. Asegúrate de tener los DMs habilitados.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estado(bot))
