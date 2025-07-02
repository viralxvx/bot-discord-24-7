import discord
from discord.ext import commands
from config import CANAL_NORMAS_ID
from mensajes import normas_texto as texto
from mensajes import normas_config as config

class NormasGenerales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mensajes_normas = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("🔧 Iniciando módulo de normas generales...")
        canal = self.bot.get_channel(CANAL_NORMAS_ID)
        if not canal:
            print(f"❌ No se encontró el canal con ID: {CANAL_NORMAS_ID}")
            return

        bloques = self.dividir_texto(texto.DESCRIPCION, 4000)

        # Buscar mensajes del bot en el canal
        try:
            mensajes_existentes = []
            async for msg in canal.history(limit=10):
                if msg.author == self.bot.user and msg.embeds:
                    mensajes_existentes.append(msg)
            mensajes_existentes = list(reversed(mensajes_existentes))  # En orden original
        except Exception as e:
            print(f"❌ Error al buscar mensajes previos del bot: {e}")
            mensajes_existentes = []

        if len(mensajes_existentes) >= len(bloques):
            print("✏️ Editando mensajes anteriores del bot...")
            for i, bloque in enumerate(bloques):
                try:
                    embed = discord.Embed(
                        title=texto.TITULO if i == 0 else None,
                        description=bloque,
                        color=discord.Color.orange()
                    )
                    if i == len(bloques) - 1 and texto.IMAGEN_URL:
                        embed.set_image(url=texto.IMAGEN_URL)

                    await mensajes_existentes[i].edit(embed=embed)
                    print(f"✅ Mensaje {i+1} editado.")
                except Exception as e:
                    print(f"❌ Error al editar el mensaje {i+1}: {e}")
        else:
            print("🧹 No se encontraron suficientes mensajes. Limpiando canal...")
            try:
                async for msg in canal.history(limit=None):
                    await msg.delete()
                print("✅ Canal limpiado con éxito.")
            except Exception as e:
                print(f"❌ Error al borrar mensajes: {e}")
                return

            print("📤 Publicando nuevos mensajes...")
            for i, bloque in enumerate(bloques):
                try:
                    embed = discord.Embed(
                        title=texto.TITULO if i == 0 else None,
                        description=bloque,
                        color=discord.Color.orange()
                    )
                    if i == len(bloques) - 1 and texto.IMAGEN_URL:
                        embed.set_image(url=texto.IMAGEN_URL)

                    msg = await canal.send(embed=embed)
                    self.mensajes_normas.append(msg)
                    print(f"✅ Embed {i+1} publicado.")
                except Exception as e:
                    print(f"❌ Error al publicar el embed {i+1}: {e}")

    def dividir_texto(self, texto_largo, max_largo):
        bloques = []
        while len(texto_largo) > max_largo:
            corte = texto_largo.rfind("\n", 0, max_largo)
            if corte == -1:
                corte = max_largo
            bloques.append(texto_largo[:corte].strip())
            texto_largo = texto_largo[corte:].strip()
        bloques.append(texto_largo.strip())
        return bloques

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_NORMAS_ID and not message.author.bot:
            try:
                await message.delete()
                print(f"🗑️ Mensaje de {message.author} eliminado en #normas-generales")
            except Exception as e:
                print(f"❌ No se pudo borrar mensaje no autorizado: {e}")

async def setup(bot):
    await bot.add_cog(NormasGenerales(bot))
