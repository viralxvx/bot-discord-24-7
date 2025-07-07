import discord
from discord.ext import commands, tasks
from mensajes.anuncios_texto import (
    TITULO_FUNCION, DESC_FUNCION, URL_FUNCION, get_update_id_funcion
)
from config import CANAL_FUNCIONES

class NuevasFunciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_funciones.start()

    @tasks.loop(minutes=5)
    async def check_funciones(self):
        update_id = get_update_id_funcion()
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

def setup(bot):
    bot.add_cog(NuevasFunciones(bot))
