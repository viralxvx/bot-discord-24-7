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
        await interaction.response.defer(ephemeral=True)
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

        embed.set_footer(text="Sistema de reputación • VX")
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        try:
            await user.send(embed=embed)
            await interaction.followup.send("✅ Te he enviado tu estado por mensaje privado.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ No pude enviarte un mensaje privado. Verifica tus ajustes de privacidad.", ephemeral=True)

    @app_commands.command(name="estadisticas", description="Ver estadísticas generales del sistema de faltas")
    async def estadisticas(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        members = interaction.guild.member_count
        keys = await self.redis.keys("faltas:*")
        usuarios_faltas = set(k.split(":")[1] for k in keys if k.count(":") == 1)

        total_faltas = 0
        for uid in usuarios_faltas:
            total_faltas += int(await self.redis.get(f"faltas:{uid}") or 0)

        baneados = 0
        expulsados = 0
        for uid in usuarios_faltas:
            estado = await self.redis.get(f"estado:{uid}")
            if estado == "Baneado":
                baneados += 1
            elif estado == "Expulsado":
                expulsados += 1

        embed = discord.Embed(
            title="📊 Estadísticas del sistema de faltas",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="👥 Miembros totales", value=f"{members}", inline=True)
        embed.add_field(name="📌 Miembros con faltas", value=f"{len(usuarios_faltas)}", inline=True)
        embed.add_field(name="📛 Total de faltas registradas", value=f"{total_faltas}", inline=False)
        embed.add_field(name="🚫 Baneados", value=f"{baneados}", inline=True)
        embed.add_field(name="❌ Expulsados", value=f"{expulsados}", inline=True)

        embed.set_footer(text="Sistema automatizado • VX")
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estado(bot))
