import discord
from discord.ext import commands
from config import CANAL_FUNCIONES, CANAL_ANUNCIOS
from utils.notificaciones import get_redis
from datetime import datetime

class AnuncioView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Ver actualización", url=url, style=discord.ButtonStyle.link))

class NuevasFunciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Solo para el canal de nuevas funciones y evita anuncios por bots (a menos que seas tú mismo)
        if (
            message.channel.id == CANAL_FUNCIONES
            and not message.author.bot  # Solo humanos, si quieres incluir el bot, quita esto
            and message.embeds  # Solo si hay embed (asume formato premium)
        ):
            redis = await get_redis()
            last_id = await redis.get("vxbot:last_funcion_update_id")
            if last_id == str(message.id):
                return  # Ya fue anunciado este mensaje

            url_funcion_real = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            canal_anuncios = self.bot.get_channel(CANAL_ANUNCIOS)
            if not canal_anuncios:
                return

            embed_anuncio = discord.Embed(
                title="📢 Nueva Funcionalidad Disponible — ¡Nuevo!",
                description=message.embeds[0].description or "",
                color=0xf1c40f
            )
            embed_anuncio.set_thumbnail(url="https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj")
            embed_anuncio.add_field(name="Tipo", value="Nueva Función", inline=True)
            embed_anuncio.add_field(name="Fecha", value=datetime.now().strftime('%d/%m/%Y'), inline=True)
            embed_anuncio.set_footer(text=f"Publicado por Equipo VX | VXbot")

            await canal_anuncios.send(embed=embed_anuncio, view=AnuncioView(url_funcion_real))
            await redis.set("vxbot:last_funcion_update_id", str(message.id))

async def setup(bot):
    await bot.add_cog(NuevasFunciones(bot))
