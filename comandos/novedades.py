import discord
from discord.ext import commands
from discord import app_commands
from utils.notificaciones import (
    obtener_no_leidos, marcar_todo_leido
)
from mensajes.anuncios_texto import LOGO_URL

class Novedades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="novedades", description="Ver tus novedades no leídas y el historial.")
    async def novedades(self, interaction: discord.Interaction):
        novedades = await obtener_no_leidos(interaction.user.id)
        if not novedades:
            await interaction.response.send_message(
                "✅ ¡Estás al día! No tienes novedades pendientes.",
                ephemeral=True
            )
            return
        embed = discord.Embed(
            title="🆕 Tus novedades pendientes",
            description="\n".join([f"• **{n['titulo']}** — [Ver]({n['url']})" for n in novedades]),
            color=0x0057b8
        )
        embed.set_thumbnail(url=LOGO_URL)
        embed.set_footer(text="VXbot | Puedes marcar todo como leído usando el botón de abajo.")
        view = NovedadesView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class NovedadesView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id

    @discord.ui.button(label="Marcar todo como leído", style=discord.ButtonStyle.success)
    async def marcar_leido(self, interaction: discord.Interaction, button: discord.ui.Button):
        await marcar_todo_leido(self.user_id)
        await interaction.response.edit_message(
            content="✅ ¡Todo marcado como leído!",
            embed=None,
            view=None
        )

async def setup(bot):
    await bot.add_cog(Anuncios(bot))

