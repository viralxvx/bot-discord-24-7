# comandos/novedades.py

import discord
from discord.ext import commands
from utils.notificaciones import (
    obtener_no_leidos, marcar_todo_leido
)
from mensajes.anuncios_texto import LOGO_URL

class Novedades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="novedades", description="Ver tus novedades no leídas y el historial.")
    async def novedades(self, ctx):
        novedades = await obtener_no_leidos(ctx.author.id)
        if not novedades:
            await ctx.respond("✅ ¡Estás al día! No tienes novedades pendientes.", ephemeral=True)
            return
        embed = discord.Embed(
            title="🆕 Tus novedades pendientes",
            description="\n".join([f"• **{n['titulo']}** — [Ver]({n['url']})" for n in novedades]),
            color=0x0057b8
        )
        embed.set_thumbnail(url=LOGO_URL)
        embed.set_footer(text="VXbot | Puedes marcar todo como leído usando el botón de abajo.")
        view = NovedadesView(ctx.author.id)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

class NovedadesView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id

    @discord.ui.button(label="Marcar todo como leído", style=discord.ButtonStyle.success)
    async def marcar_leido(self, button, interaction):
        await marcar_todo_leido(self.user_id)
        await interaction.response.edit_message(content="✅ ¡Todo marcado como leído!", embed=None, view=None)

def setup(bot):
    bot.add_cog(Novedades(bot))
