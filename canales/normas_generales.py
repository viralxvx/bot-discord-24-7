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
        print("🔧 Iniciando módulo de normas generales...")
        canal = self.bot.get_channel(CANAL_NORMAS_ID)

        if not canal:
            print(f"❌ No se encontró el canal con ID: {CANAL_NORMAS_ID}")
            return

        try:
            print("🧹 Borrando mensajes existentes en el canal...")
            async for msg in canal.history(limit=None):
                await msg.delete()
            print("✅ Canal limpiado con éxito.")
        except Exception as e:
            print(f"❌ Error al borrar mensajes en el canal: {e}")
            return

        # Crear el embed
        try:
            embed = discord.Embed(
                title=texto.TITULO,
                description=texto.DESCRIPCION,
                color=discord.Color.orange()
            )
            if texto.IMAGEN_URL:
                embed.set_image(url=texto.IMAGEN_URL)

            self.mensaje_normas = await canal.send(embed=embed)
            print("✅ Normas publicadas correctamente en el canal.")
        except Exception as e:
            print(f"❌ Error al enviar el mensaje de normas: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_NORMAS_ID and not message.author.bot:
            try:
                await message.delete()
                print(f"🗑️ Mensaje de {message.author} eliminado en #normas-generales")
            except Exception as e:
                print(f"❌ No se pudo borrar un mensaje no autorizado: {e}")

async def setup(bot):
    await bot.add_cog(NormasGenerales(bot))
