import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_FALTAS_ID, ADMIN_ID, REDIS_URL
from utils.panel_embed import actualizar_panel_faltas
import redis

class MigrarPaneles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(
        name="migrar_paneles",
        description="Migra todos los paneles viejos de faltas al formato premium (solo admin)."
    )
    async def migrar_paneles(self, interaction: discord.Interaction):
        # Solo el admin puede ejecutar
        if interaction.user.id != int(ADMIN_ID):
            await interaction.response.send_message(
                "❌ Solo el administrador principal puede migrar los paneles.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔄 Migrando paneles viejos al nuevo formato premium. Esto puede tardar unos minutos...",
            ephemeral=True
        )

        canal = interaction.guild.get_channel(CANAL_FALTAS_ID)
        if not canal:
            await interaction.followup.send("❌ No se encontró el canal de faltas.", ephemeral=True)
            return

        migrados = 0
        for member in interaction.guild.members:
            if member.bot:
                continue
            try:
                await actualizar_panel_faltas(self.bot, member)
                migrados += 1
            except Exception as e:
                print(f"❌ Error migrando panel de {member.display_name}: {e}")

        await interaction.followup.send(
            f"✅ Paneles migrados: {migrados}. ¡Todos los mensajes están ahora en el nuevo formato premium!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(MigrarPaneles(bot))
