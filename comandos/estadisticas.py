import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ID
from mensajes.comandos_texto import generar_embed_estadisticas
import redis
import os

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        redis_url = os.getenv("REDIS_URL")
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)

    @app_commands.command(name="estadisticas", description="Ver estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != int(ADMIN_ID):
                await interaction.response.send_message("❌ Solo los administradores pueden usar este comando.", ephemeral=True)
                return

            await interaction.response.defer(thinking=True)

            guild = interaction.guild
            miembros = [m for m in guild.members if not m.bot]

            total_miembros = len(miembros)

            # Corregido: Obtener lista de baneados correctamente
            total_baneados = [ban async for ban in guild.bans()]
            total_baneados_count = len(total_baneados)

            # Contar usuarios expulsados
            total_expulsados = 0
            for miembro in miembros:
                status = self.redis.hget(f"usuario:{miembro.id}", "estado")
                if status and status.lower() == "expulsado":
                    total_expulsados += 1

            embed = generar_embed_estadisticas(total_miembros, total_baneados_count, total_expulsados)

            await interaction.followup.send(embed=embed, ephemeral=True)

            # También enviar por DM como respaldo
            try:
                await interaction.user.send(embed=embed)
            except:
                print(f"❌ No se pudo enviar DM a {interaction.user.display_name}")

        except Exception as e:
            print(f"❌ Error en /estadisticas: {e}")
            await interaction.followup.send("❌ Hubo un error al obtener las estadísticas. Contacta a un administrador.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
