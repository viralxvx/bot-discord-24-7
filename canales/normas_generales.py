import discord
from discord.ext import commands
from config import CANAL_NORMAS_ID
from mensajes import normas_texto as texto
from mensajes import normas_config as config

class NormasGenerales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("🔧 Iniciando módulo de normas generales...")
        canal = self.bot.get_channel(CANAL_NORMAS_ID)
        if not canal:
            print(f"❌ No se encontró el canal con ID: {CANAL_NORMAS_ID}")
            return

        try:
            # Buscar mensajes anteriores del bot
            mensajes_existentes = []
            async for msg in canal.history(limit=10):
                if msg.author == self.bot.user and msg.embeds:
                    mensajes_existentes.append(msg)
            mensajes_existentes = list(reversed(mensajes_existentes))  # Orden correcto
        except Exception as e:
            print(f"❌ Error al buscar mensajes previos: {e}")
            mensajes_existentes = []

        # Crear los 2 embeds
        embeds = []

        embed1 = discord.Embed(
            title=texto.TITULO,
            description=texto.DESCRIPCION_BLOQUE_1,
            color=discord.Color.orange()
        )
        embeds.append(embed1)

        embed2 = discord.Embed(
            description=texto.DESCRIPCION_BLOQUE_2,
            color=discord.Color.orange()
        )
        if texto.IMAGEN_URL:
            embed2.set_image(url=texto.IMAGEN_URL)
        embeds.append(embed2)

        if len(mensajes_existentes) >= 2:
            print("✏️ Editando mensajes anteriores...")
            for i in range(2):
                try:
                    await mensajes_existentes[i].edit(embed=embeds[i])
                    print(f"✅ Embed {i+1} editado.")
                except Exception as e:
                    print(f"❌ Error al editar el embed {i+1}: {e}")
        else:
            print("🧹 No se encontraron suficientes mensajes. Limpiando canal...")
            try:
                async for msg in canal.history(limit=None):
                    await msg.delete()
                print("✅ Canal limpiado.")
            except Exception as e:
                print(f"❌ Error al borrar mensajes: {e}")
                return

            print("📤 Publicando nuevos embeds...")
            for i, embed in enumerate(embeds):
                try:
                    await canal.send(embed=embed)
                    print(f"✅ Embed {i+1} publicado.")
                except Exception as e:
                    print(f"❌ Error al publicar el embed {i+1}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_NORMAS_ID and not message.author.bot:
            try:
                await message.delete()
                print(f"🗑️ Mensaje eliminado de {message.author} en #normas-generales")
            except Exception as e:
                print(f"❌ No se pudo borrar mensaje no autorizado: {e}")

async def setup(bot):
    await bot.add_cog(NormasGenerales(bot))
