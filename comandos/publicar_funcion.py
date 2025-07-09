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
        titulo="Título de la función",
        descripcion="Descripción o detalles de la función (usa Markdown si deseas)"
    )
    async def publicar_funcion(
        self,
        interaction: discord.Interaction,
        titulo: str,
        descripcion: str
    ):
        # Solo admins autorizados
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

        embed = discord.Embed(
            title=titulo,
            description=descripcion,
            color=0x0057b8
        )
        embed.set_thumbnail(url="https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj")
        embed.set_footer(text="Publicado por VXbot | Sistema premium")
        mensaje = await canal_funciones.send(embed=embed)

        url_funcion_real = f"https://discord.com/channels/{canal_funciones.guild.id}/{canal_funciones.id}/{mensaje.id}"

        await interaction.response.send_message(
            f"✅ ¡Función publicada con éxito! [Ver publicación en el canal]({url_funcion_real})",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PublicarFuncion(bot))
