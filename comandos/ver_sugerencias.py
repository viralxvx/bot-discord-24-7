import discord
from discord.ext import commands
from discord import app_commands
from config import ADMIN_ID, REDIS_URL, CANAL_COMANDOS_ID
from mensajes.sugerencias_texto import generar_embed_sugerencia
import redis
import json
from datetime import datetime

class VerSugerencias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(name="ver_sugerencias", description="Revisa todas las sugerencias enviadas")
    async def ver_sugerencias(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Solo administradores pueden usar este comando.", ephemeral=True)
            return

        if interaction.channel_id != CANAL_COMANDOS_ID:
            await interaction.response.send_message("❌ Solo puede usarse en el canal 💻comandos.", ephemeral=True)
            return

        claves = self.redis.keys("sugerencia:*")
        if not claves:
            await interaction.response.send_message("📭 No hay sugerencias registradas.", ephemeral=True)
            return

        claves.sort(reverse=True)  # Mostramos las más recientes primero
        embeds = []
        for clave in claves[:5]:
            datos = self.redis.get(clave)
            if not datos:
                continue
            try:
                sug = json.loads(datos)
                embed = generar_embed_sugerencia(sug, clave)
                embeds.append(embed)
            except Exception as e:
                print(f"Error al procesar sugerencia {clave}: {e}")

        if not embeds:
            await interaction.response.send_message("❌ No se pudo generar el panel.", ephemeral=True)
            return

        await interaction.response.send_message(embeds=embeds, ephemeral=True)

async def setup(bot):
    await bot.add_cog(VerSugerencias(bot))
