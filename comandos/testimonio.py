# comandos/testimonio.py

import discord
from discord import app_commands
from discord.ext import commands
from config import get_env_int
from utils.redis_conn import redis_conn
from utils.formatter import crear_embed_testimonio

CANAL_TESTIMONIOS = get_env_int("CANAL_TESTIMONIOS")

class Testimonio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="testimonio", description="Comparte tu experiencia con VX")
    @app_commands.describe(
        contenido="Tu testimonio (experiencia, resultados, aprendizaje)",
        tipo="Categoría principal del testimonio",
        tiempo="¿En cuánto tiempo lograste resultados?",
        impacto="Resultados alcanzados (ej: 100k vistas, 3 clientes)",
        calificacion="De 1 a 5 estrellas",
        destacar="¿Qué fue lo que más te gustó?",
        anonimo="¿Deseas que sea publicado anónimamente?"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="💸 Monetización", value="monetizacion"),
        app_commands.Choice(name="📈 Viralidad", value="viralidad"),
        app_commands.Choice(name="🧠 Mentalidad", value="mentalidad"),
        app_commands.Choice(name="🚀 Progreso personal", value="progreso"),
    ])
    async def testimonio(
        self,
        interaction: discord.Interaction,
        contenido: str,
        tipo: app_commands.Choice[str],
        tiempo: str,
        impacto: str,
        calificacion: app_commands.Range[int, 1, 5],
        destacar: str = "",
        anonimo: bool = False
    ):
        await interaction.response.defer(ephemeral=True)

        autor_id = interaction.user.id
        canal = interaction.guild.get_channel(CANAL_TESTIMONIOS)

        if not canal:
            await interaction.followup.send("❌ No se pudo encontrar el canal de testimonios.", ephemeral=True)
            return

        # Guardar en Redis
        redis_conn.hset(f"vx:testimonio:{autor_id}", mapping={
            "contenido": contenido,
            "tipo": tipo.value,
            "tiempo": tiempo,
            "impacto": impacto,
            "calificacion": calificacion,
            "destacar": destacar,
            "anonimo": anonimo
        })

        # Crear embed
        embed = crear_embed_testimonio(
            usuario=interaction.user,
            contenido=contenido,
            tipo=tipo.value,
            tiempo=tiempo,
            impacto=impacto,
            calificacion=calificacion,
            destacar=destacar,
            anonimo=anonimo
        )

        mensaje = await canal.send(embed=embed)
        redis_conn.hset(f"vx:testimonio:{autor_id}", "mensaje_id", mensaje.id)

        await interaction.followup.send("✅ ¡Gracias por compartir tu experiencia! Tu testimonio ya fue publicado en el canal oficial.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Testimonio(bot))
