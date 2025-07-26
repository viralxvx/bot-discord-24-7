# comandos/publicar_funcion.py

import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_FUNCIONES, ADMIN_ID

class PublicarFuncion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="publicar_funcion",
        description="(Solo admins) Publica una nueva función con formato premium."
    )
    @app_commands.describe(
        titulo="Título visual de la función",
        descripcion="Texto completo (puede venir desde Word o Docs, se adaptará automáticamente)"
    )
    async def publicar_funcion(
        self,
        interaction: discord.Interaction,
        titulo: str,
        descripcion: str
    ):
        if interaction.user.id != ADMIN_ID and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "⛔ No tienes permisos para usar este comando.",
                ephemeral=True
            )
            return

        canal_funciones = interaction.guild.get_channel(CANAL_FUNCIONES)
        if not canal_funciones:
            await interaction.response.send_message(
                "❌ No se encontró el canal de nuevas funciones.",
                ephemeral=True
            )
            return

        # 🔧 Limpiar triple comillas, separadores y espacios duplicados
        texto = descripcion.replace('"""', '').replace("```", '').strip()
        texto = texto.replace("\r\n", "\n").replace("\r", "\n")  # Estilo Word/Docs
        bloques = [bloque.strip() for bloque in texto.split("\n\n") if bloque.strip()]

        embed = discord.Embed(
            title=f"🎉 {titulo.strip()}",
            color=0x0057b8
        )
        embed.set_thumbnail(url="https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj")

        if len(bloques) > 1:
            for i, bloque in enumerate(bloques):
                embed.add_field(name="‎" if i == 0 else "​", value=bloque, inline=False)
        else:
            embed.description = texto

        embed.set_footer(text="Publicado por VXbot | Sistema premium")
        mensaje = await canal_funciones.send(embed=embed)

        url_funcion_real = f"https://discord.com/channels/{canal_funciones.guild.id}/{canal_funciones.id}/{mensaje.id}"

        await interaction.response.send_message(
            f"✅ ¡Función publicada con éxito! [Ver en canal]({url_funcion_real})",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PublicarFuncion(bot))
