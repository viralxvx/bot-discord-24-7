# comandos/ver_sugerencias.py
import discord
from discord.ext import commands
from discord import app_commands
from config import REDIS_URL, ADMIN_ID
import redis

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

ESTADOS = {
    "pendiente": "🕐 Pendiente",
    "hecha": "✅ Hecha",
    "descartada": "❌ Descartada"
}

class VerSugerencias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ver_sugerencias_test", description="Revisa y gestiona las sugerencias enviadas por los usuarios")
    async def ver_sugerencias(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Solo los administradores pueden usar este comando.", ephemeral=True)
            return

        sugerencias = redis_client.hgetall("soporte:sugerencias")

        if not sugerencias:
            await interaction.response.send_message("📭 No hay sugerencias registradas.", ephemeral=True)
            return

        # Convertir a lista de tuplas ordenadas por fecha
        sugerencias_ordenadas = sorted(
            [(k, eval(v)) for k, v in sugerencias.items()],
            key=lambda item: item[1]["timestamp"],
            reverse=True
        )

        embeds = []
        for user_id, data in sugerencias_ordenadas[:10]:  # Limite por ahora a 10
            user = self.bot.get_user(int(user_id))
            estado = ESTADOS.get(data.get("estado", "pendiente"), "🕐 Pendiente")
            embed = discord.Embed(
                title=f"📬 Sugerencia de {user.name if user else user_id}",
                description=data.get("mensaje", "(sin mensaje)"),
                color=discord.Color.blue()
            )
            embed.add_field(name="Estado", value=estado, inline=True)
            embed.add_field(name="Fecha", value=data.get("fecha", "N/A"), inline=True)
            embed.set_footer(text=f"ID: {user_id}")
            embeds.append(embed)

        await interaction.response.send_message(embeds=embeds, ephemeral=True)

async def setup(bot):
    await bot.add_cog(VerSugerencias(bot))
