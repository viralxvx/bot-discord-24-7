import discord
from discord import app_commands
from discord.ext import commands
from config import REDIS_URL, ADMIN_ID
import redis.asyncio as redis
import datetime

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema de faltas")
    async def estado(self, interaction: discord.Interaction):
        print(f"✅ Ejecutando comando /estado por: {interaction.user.id}")
        await interaction.response.defer(ephemeral=False)
        user = interaction.user
        estado = await self.redis.get(f"estado:{user.id}") or "Activo"
        total_faltas = await self.redis.get(f"faltas:{user.id}") or 0
        mes = datetime.datetime.utcnow().strftime("%Y-%m")
        faltas_mes = await self.redis.get(f"faltas:{user.id}:{mes}") or 0
        timestamp = await self.redis.get(f"ultimo_registro:{user.id}")

        embed = discord.Embed(
            title=f"📋 Estado actual de {user.display_name}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="🟢 Estado", value=f"`{estado}`", inline=True)
        embed.add_field(name="❗ Total de faltas", value=f"`{total_faltas}`", inline=True)
        embed.add_field(name="📅 Faltas este mes", value=f"`{faltas_mes}`", inline=True)

        if timestamp:
            fecha = datetime.datetime.fromtimestamp(int(timestamp))
            embed.add_field(name="🕓 Última falta", value=f"<t:{int(fecha.timestamp())}:R>", inline=False)

        embed.set_footer(text="(Depuración pública temporal) Sistema de reputación • VX")
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Estado(bot))
