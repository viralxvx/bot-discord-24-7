import discord
from discord.ext import commands, tasks
from mensajes.anuncios_texto import (
    TITULO_FUNCION, DESC_FUNCION, URL_FUNCION, get_update_id_funcion
)
from config import CANAL_FUNCIONES
from utils.notificaciones import get_redis

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
            return  # Ya está publicado, no repetir

        anuncios = self.bot.get_cog('Anuncios')
        if anuncios is not None:
            await anuncios.enviar_anuncio(
                tipo="Nueva Función",
                titulo=TITULO_FUNCION,
                descripcion=DESC_FUNCION,
                url_update=URL_FUNCION,
                update_id=update_id,
                autor="Equipo VX"
            )
            await redis.set("vxbot:last_funcion_update_id", update_id)

async def setup(bot):
    await bot.add_cog(NuevasFunciones(bot))
