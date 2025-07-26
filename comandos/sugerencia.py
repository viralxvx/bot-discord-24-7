# comandos/sugerencia.py

import discord
from discord import app_commands
from discord.ext import commands
import datetime
import uuid
import os
from utils.redis_conn import redis_conn
from config import CANAL_MEJORA_VX_ID, ADMIN_ROLE_ID

class Sugerencia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sugerencia", description="Envía una sugerencia pública para mejorar VX")
    @app_commands.describe(
        tipo="Selecciona el tipo de sugerencia",
        contenido="Escribe tu sugerencia de forma clara y específica"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="💡 Idea Nueva", value="idea"),
        app_commands.Choice(name="⚙️ Mejora del sistema", value="mejora"),
        app_commands.Choice(name="🐞 Reporte de error", value="error"),
        app_commands.Choice(name="📢 Sugerencia general", value="general"),
    ])
    async def sugerencia(self, interaction: discord.Interaction, tipo: app_commands.Choice[str], contenido: str):
        await interaction.response.defer(ephemeral=True)

        canal = self.bot.get_channel(CANAL_MEJORA_VX_ID)
        if not canal:
            await interaction.followup.send("❌ No se encontró el canal de sugerencias. Contacta a un administrador.")
            return

        sugerencia_id = str(uuid.uuid4())[:8]
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        embed = discord.Embed(
            title=f"🧠 NUEVA SUGERENCIA: {tipo.name}",
            description=contenido,
            color=discord.Color.blurple()
        )
        embed.set_author(name=f"{interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Sugerencia ID: {sugerencia_id} • Enviada el {timestamp}")

        mensaje = await canal.send(embed=embed)

        # Guardar en Redis
        redis_conn.hset(f"sugerencia:{sugerencia_id}", mapping={
            "user_id": str(interaction.user.id),
            "mensaje_id": str(mensaje.id),
            "canal_id": str(canal.id),
            "tipo": tipo.value,
            "contenido": contenido,
            "estado": "pendiente",
            "fecha": timestamp
        })

        await interaction.followup.send("✅ Tu sugerencia ha sido publicada en el canal de mejoras.")

async def setup(bot):
    await bot.add_cog(Sugerencia(bot))
