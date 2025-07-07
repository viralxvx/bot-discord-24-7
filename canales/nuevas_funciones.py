import discord
from discord.ext import commands, tasks
from mensajes.anuncios_texto import (
    TITULO_FUNCION, DESC_FUNCION, get_update_id_funcion
)
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
        self.check_funciones.start()

    @tasks.loop(minutes=5)
    async def check_funciones(self):
        update_id = get_update_id_funcion()
        redis = await get_redis()
        last_id = await redis.get("vxbot:last_funcion_update_id")
        if last_id == update_id:
            return  # Ya publicado

        canal_funciones = self.bot.get_channel(CANAL_FUNCIONES)
        canal_anuncios = self.bot.get_channel(CANAL_ANUNCIOS)
        if not canal_funciones or not canal_anuncios:
            return

        # Publica la nueva función
        embed_funcion = discord.Embed(
            title=TITULO_FUNCION,
            description=DESC_FUNCION,
            color=0x0057b8
        )
        embed_funcion.set_footer(text=f"Publicado por Equipo VX | VXbot")
        mensaje_funcion = await canal_funciones.send(embed=embed_funcion)

        url_funcion_real = f"https://discord.com/channels/{canal_funciones.guild.id}/{canal_funciones.id}/{mensaje_funcion.id}"

        # Publica el anuncio con botón
        embed_anuncio = discord.Embed(
            title=f"📢 {TITULO_FUNCION} — ¡Nuevo!",
            description=DESC_FUNCION,
            color=0xf1c40f
        )
        embed_anuncio.set_thumbnail(url="https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj")
        embed_anuncio.add_field(name="Tipo", value="Nueva Función", inline=True)
        embed_anuncio.add_field(name="Fecha", value=datetime.now().strftime('%d/%m/%Y'), inline=True)
        embed_anuncio.set_footer(text=f"Publicado por Equipo VX | VXbot")

        await canal_anuncios.send(embed=embed_anuncio, view=AnuncioView(url_funcion_real))
        await redis.set("vxbot:last_funcion_update_id", update_id)

async def setup(bot):
    await bot.add_cog(NuevasFunciones(bot))
