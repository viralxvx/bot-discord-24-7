import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ID, REDIS_URL, CANAL_COMANDOS_ID
from mensajes.comandos_texto import generar_embed_estadisticas
import redis

class Estadisticas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(name="estadisticas", description="Ver estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        # Solo admin puede ejecutar
        if interaction.user.id != int(ADMIN_ID):
            await interaction.response.send_message("❌ Solo los administradores pueden usar este comando.", ephemeral=True)
            return

        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal de comandos.",
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer(thinking=True)

            guild = interaction.guild
            miembros = [m for m in guild.members if not m.bot]
            total_miembros = len(miembros)

            # Leer todos los usuarios con registro de estado en Redis
            keys = self.redis.keys("usuario:*")
            estados = {
                "activo": 0,
                "baneado": 0,
                "expulsado": 0,
                "desercion": 0
            }
            for key in keys:
                estado = (self.redis.hget(key, "estado") or "activo").lower()
                if estado in estados:
                    estados[estado] += 1
                else:
                    estados["activo"] += 1  # Fallback

            embed = generar_embed_estadisticas(
                total_miembros,
                estados["baneado"],
                estados["expulsado"],
                estados["desercion"],
                estados["activo"]
            )

            # Envía en canal de comandos y autoelimina a los 10 min
            msg = await interaction.followup.send(embed=embed, ephemeral=False, delete_after=600)

            # También lo envía por DM al admin como respaldo
            try:
                await interaction.user.send(embed=embed)
            except Exception:
                print(f"❌ No se pudo enviar DM a {interaction.user.display_name}")

        except Exception as e:
            print(f"❌ Error en /estadisticas: {e}")
            await interaction.followup.send("❌ Hubo un error al obtener las estadísticas. Contacta a un administrador.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estadisticas(bot))
