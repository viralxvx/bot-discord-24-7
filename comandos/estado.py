import discord
from discord import app_commands
from discord.ext import commands
import redis
import logging
from config import REDIS_URL, CANAL_COMANDOS_ID
from mensajes.comandos_texto import generar_embed_estado

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(name="estado", description="Consulta tu estado de reputación en el sistema de faltas.")
    async def estado(self, interaction: discord.Interaction):
        usuario = interaction.user

        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal de comandos.",
                ephemeral=True
            )
            return

        try:
            # Obtener datos desde Redis
            data = self.redis.hgetall(f"faltas:{usuario.id}")

            # Establecer valores por defecto si faltan
            faltas_total = int(data.get("faltas_total", 0))
            faltas_mes = int(data.get("faltas_mes", 0))
            estado = data.get("estado", "Activo")

            data_usuario = {
                "estado": estado,
                "faltas_total": faltas_total,
                "faltas_mes": faltas_mes
            }

            embed = generar_embed_estado(usuario, data_usuario)

            await interaction.response.send_message(embed=embed, delete_after=600)

            try:
                await usuario.send(embed=embed)
            except:
                logging.warning(f"⚠️ No se pudo enviar DM a {usuario.name}.")

        except Exception as e:
            logging.error(f"❌ Error en /estado: {e}")
            await interaction.response.send_message("❌ Hubo un error al procesar tu estado. Contacta a un moderador.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estado(bot))
