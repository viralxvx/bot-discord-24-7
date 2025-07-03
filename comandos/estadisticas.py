import discord
from discord import app_commands
from discord.ext import commands
import redis
import os

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

    @app_commands.command(name="estadisticas", description="Muestra estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        user = interaction.user
        guild_id = os.getenv("GUILD_ID")
        print(f"📊 [LOG] Usuario ejecutó /estadisticas: {user.name} ({user.id})")

        # Obtener claves que correspondan a usuarios
        miembros = self.redis.keys(f"{guild_id}:faltas:*")
        total_miembros = len(miembros)

        baneados = 0
        expulsados = 0
        activos = 0

        for clave in miembros:
            estado = self.redis.hget(clave, "estado")
            if estado == "baneado":
                baneados += 1
            elif estado == "expulsado":
                expulsados += 1
            else:
                activos += 1

        embed = discord.Embed(
            title="📊 Estadísticas Generales del Servidor",
            color=discord.Color.blue()
        )
        embed.add_field(name="👥 Total de miembros", value=total_miembros, inline=True)
        embed.add_field(name="🟢 Activos", value=activos, inline=True)
        embed.add_field(name="⛔ Baneados", value=baneados, inline=True)
        embed.add_field(name="🚫 Expulsados", value=expulsados, inline=True)
        embed.set_footer(text="Sistema automatizado de control • VX")

        try:
            await user.send(embed=embed)
            await interaction.response.send_message("✅ Te envié las estadísticas por DM.", ephemeral=True)
        except Exception as e:
            print(f"❌ Error al enviar DM: {e}")
            await interaction.response.send_message("❌ No pude enviarte las estadísticas por DM. Asegúrate de tener los mensajes privados activados.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
