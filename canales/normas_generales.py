import discord
from discord.ext import commands
from config import CANAL_NORMAS_ID, CANAL_LOGS_ID
from mensajes import normas_texto as texto
from mensajes import normas_config as config
from utils.logger import log_discord  # <-- Logger universal

class NormasGenerales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await log_discord(self.bot, "🔧 Iniciando módulo de normas generales...", CANAL_LOGS_ID, "info", "NormasGenerales")
        canal = self.bot.get_channel(CANAL_NORMAS_ID)
        if not canal:
            await log_discord(self.bot, f"❌ No se encontró el canal con ID: {CANAL_NORMAS_ID}", CANAL_LOGS_ID, "error", "NormasGenerales")
            return

        try:
            mensajes_existentes = []
            async for msg in canal.history(limit=10):
                if msg.author == self.bot.user and msg.embeds:
                    mensajes_existentes.append(msg)
            mensajes_existentes = list(reversed(mensajes_existentes))
        except Exception as e:
            await log_discord(self.bot, f"❌ Error al buscar mensajes previos: {e}", CANAL_LOGS_ID, "error", "NormasGenerales")
            mensajes_existentes = []

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
            await log_discord(self.bot, "✏️ Editando mensajes anteriores...", CANAL_LOGS_ID, "info", "NormasGenerales")
            for i in range(2):
                try:
                    await mensajes_existentes[i].edit(embed=embeds[i])
                    await log_discord(self.bot, f"✅ Embed {i+1} editado.", CANAL_LOGS_ID, "success", "NormasGenerales")
                except Exception as e:
                    await log_discord(self.bot, f"❌ Error al editar el embed {i+1}: {e}", CANAL_LOGS_ID, "error", "NormasGenerales")
        else:
            await log_discord(self.bot, "🧹 No se encontraron suficientes mensajes. Limpiando canal...", CANAL_LOGS_ID, "warning", "NormasGenerales")
            try:
                async for msg in canal.history(limit=None):
                    await msg.delete()
                await log_discord(self.bot, "✅ Canal limpiado.", CANAL_LOGS_ID, "success", "NormasGenerales")
            except Exception as e:
                await log_discord(self.bot, f"❌ Error al borrar mensajes: {e}", CANAL_LOGS_ID, "error", "NormasGenerales")
                return

            await log_discord(self.bot, "📤 Publicando nuevos embeds...", CANAL_LOGS_ID, "info", "NormasGenerales")
            for i, embed in enumerate(embeds):
                try:
                    await canal.send(embed=embed)
                    await log_discord(self.bot, f"✅ Embed {i+1} publicado.", CANAL_LOGS_ID, "success", "NormasGenerales")
                except Exception as e:
                    await log_discord(self.bot, f"❌ Error al publicar el embed {i+1}: {e}", CANAL_LOGS_ID, "error", "NormasGenerales")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_NORMAS_ID and not message.author.bot:
            try:
                await message.delete()
                await log_discord(self.bot, f"🗑️ Mensaje eliminado de {message.author} en #normas-generales", CANAL_LOGS_ID, "info", "NormasGenerales")
            except Exception as e:
                await log_discord(self.bot, f"❌ No se pudo borrar mensaje no autorizado: {e}", CANAL_LOGS_ID, "error", "NormasGenerales")

async def setup(bot):
    await bot.add_cog(NormasGenerales(bot))
