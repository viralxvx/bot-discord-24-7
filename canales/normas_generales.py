import discord
from discord.ext import commands
from config import CANAL_NORMAS_ID
from mensajes import normas_texto as texto
from mensajes import normas_config as config

class NormasGenerales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mensaje_normas = None

    @commands.Cog.listener()
    async def on_ready(self):
        canal = self.bot.get_channel(CANAL_NORMAS_ID)
        if not canal:
            print(f"❌ No se encontró el canal de normas: {CANAL_NORMAS_ID}")
            return

        # Borrar TODOS los mensajes (fijados, bot y usuarios)
        try:
            async for msg in canal.history(limit=None):
                await msg.delete()
        except Exception as e:
            print(f"❌ Error al borrar mensajes en {canal.name}: {e}")

        # Crear embed
        embed = discord.Embed(
            title=texto.TITULO,
            description=texto.DESCRIPCION,
            color=discord.Color.orange()
        )
        if texto.IMAGEN_URL:
            embed.set_image(url=texto.IMAGEN_URL)

        # Enviar mensaje nuevo y guardar
        self.mensaje_normas = await canal.send(embed=embed)
        print("✅ Normas publicadas correctamente")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_NORMAS_ID and not message.author.bot:
            await message.delete()

async def setup(bot):
    await bot.add_cog(NormasGenerales(bot))
