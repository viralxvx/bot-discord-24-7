# comandos/ver_sugerencias.py

import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ROLE_ID
from utils.redis_conn import redis_conn

class VerSugerencias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ver_sugerencias", description="Revisa las sugerencias del canal 🧠 mejora-vx (solo admins)")
    async def ver_sugerencias(self, interaction: discord.Interaction):
        if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Buscar claves de sugerencias
        claves = redis_conn.keys("sugerencia:*")
        if not claves:
            await interaction.followup.send("📭 No hay sugerencias registradas.")
            return

        # Crear embed resumen
        embeds = []
        for clave in claves[:10]:  # Solo muestra las primeras 10 para no saturar
            data = redis_conn.hgetall(clave)
            estado = data.get("estado", "pendiente")
            tipo = data.get("tipo", "sin_tipo")
            contenido = data.get("contenido", "Sin contenido.")
            autor_id = data.get("user_id", None)
            fecha = data.get("fecha", "sin fecha")
            sugerencia_id = clave.split(":")[-1]

            embed = discord.Embed(
                title=f"🧠 SUGERENCIA #{sugerencia_id}",
                description=contenido,
                color=discord.Color.orange() if estado == "pendiente" else (
                    discord.Color.green() if estado == "hecha" else discord.Color.red()
                )
            )
            embed.add_field(name="Tipo", value=tipo.capitalize(), inline=True)
            embed.add_field(name="Estado", value=estado.capitalize(), inline=True)
            embed.add_field(name="Fecha", value=fecha, inline=False)
            if autor_id:
                embed.set_footer(text=f"Autor: <@{autor_id}> • ID: {sugerencia_id}")
            embeds.append(embed)

        await interaction.followup.send(embeds=embeds)

    @app_commands.command(name="marcar_sugerencia", description="Marca una sugerencia como hecha, pendiente o descartada")
    @app_commands.describe(
        id="ID de la sugerencia (visible en el embed)",
        estado="Nuevo estado a asignar"
    )
    @app_commands.choices(estado=[
        app_commands.Choice(name="✅ Hecha", value="hecha"),
        app_commands.Choice(name="🟢 Pendiente", value="pendiente"),
        app_commands.Choice(name="🔴 Descartada", value="descartada"),
    ])
    async def marcar_sugerencia(self, interaction: discord.Interaction, id: str, estado: app_commands.Choice[str]):
        if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return

        clave = f"sugerencia:{id}"
        if not redis_conn.exists(clave):
            await interaction.response.send_message("❌ No se encontró esa sugerencia.", ephemeral=True)
            return

        redis_conn.hset(clave, "estado", estado.value)
        await interaction.response.send_message(f"✅ Sugerencia `{id}` marcada como **{estado.name}**.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VerSugerencias(bot))
