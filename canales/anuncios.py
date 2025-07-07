import discord
from discord.ext import commands
from mensajes.anuncios_texto import (
    EMBED_ANUNCIO_TEMPLATE, EMBED_RESUMEN_REINGRESO, LOGO_URL
)
from utils.notificaciones import (
    registrar_novedad, obtener_no_leidos,
    usuario_ausente, registrar_reingreso
)
from config import CANAL_ANUNCIOS
from datetime import datetime

class Anuncios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def enviar_anuncio(self, tipo, titulo, descripcion, url_update, update_id, autor=None):
        canal = self.bot.get_channel(CANAL_ANUNCIOS)
        if not canal:
            return
        embed = EMBED_ANUNCIO_TEMPLATE(
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            url=url_update,
            autor=autor or "VXbot",
            fecha=datetime.now(),
            logo_url=LOGO_URL
        )
        mensaje = await canal.send(embed=embed)
        await registrar_novedad(update_id, tipo, titulo, descripcion, url_update, mensaje.id)

    async def resumen_reingreso(self, member):
        novedades = await obtener_no_leidos(member.id)
        if novedades:
            embed = EMBED_RESUMEN_REINGRESO(member, novedades, LOGO_URL)
            try:
                await member.send(embed=embed)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if await usuario_ausente(member.id):
            await registrar_reingreso(member.id)
            await self.resumen_reingreso(member)

def setup(bot):
    bot.add_cog(Anuncios(bot))
