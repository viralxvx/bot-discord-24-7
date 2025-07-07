import discord
from discord.ext import commands
from config import CANAL_NORMAS_ID, CANAL_LOGS_ID, CANAL_ANUNCIOS
from mensajes import normas_texto as texto
from utils.logger import log_discord
from utils.notificaciones import registrar_novedad, get_redis
from datetime import datetime
import hashlib

class AnuncioView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Ver normas actualizadas", url=url, style=discord.ButtonStyle.link))

class NormasGenerales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._ultimo_update_id = None

    @commands.Cog.listener()
    async def on_ready(self):
        await log_discord(self.bot, "🔧 Iniciando módulo de normas generales...", CANAL_LOGS_ID, "info", "NormasGenerales")
        canal = self.bot.get_channel(CANAL_NORMAS_ID)
        canal_anuncios = self.bot.get_channel(CANAL_ANUNCIOS)
        if not canal or not canal_anuncios:
            await log_discord(self.bot, f"❌ No se encontró el canal de normas o anuncios.", CANAL_LOGS_ID, "error", "NormasGenerales")
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

        texto_update = texto.DESCRIPCION_BLOQUE_1 + (texto.DESCRIPCION_BLOQUE_2 or "")
        update_id = hashlib.sha256(texto_update.encode("utf-8")).hexdigest()

        notificar_cambio = False
        mensaje_principal = None

        if len(mensajes_existentes) >= 2:
            await log_discord(self.bot, "✏️ Editando mensajes anteriores...", CANAL_LOGS_ID, "info", "NormasGenerales")
            for i in range(2):
                try:
                    old_content = mensajes_existentes[i].embeds[0].description if mensajes_existentes[i].embeds else ""
                    await mensajes_existentes[i].edit(embed=embeds[i])
                    await log_discord(self.bot, f"✅ Embed {i+1} editado.", CANAL_LOGS_ID, "success", "NormasGenerales")
                    if embeds[i].description != old_content:
                        notificar_cambio = True
                    if i == 0:
                        mensaje_principal = mensajes_existentes[i]
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
                    msg = await canal.send(embed=embed)
                    await log_discord(self.bot, f"✅ Embed {i+1} publicado.", CANAL_LOGS_ID, "success", "NormasGenerales")
                    notificar_cambio = True
                    if i == 0:
                        mensaje_principal = msg
                except Exception as e:
                    await log_discord(self.bot, f"❌ Error al publicar el embed {i+1}: {e}", CANAL_LOGS_ID, "error", "NormasGenerales")

        # --- Notificación premium con botón solo si hay cambio y no es repetido ---
        redis = await get_redis()
        last_id = await redis.get("vxbot:last_normas_update_id")

        if (not last_id or last_id != update_id or notificar_cambio) and mensaje_principal:
            await redis.set("vxbot:last_normas_update_id", update_id)
            try:
                url_real = f"https://discord.com/channels/{canal.guild.id}/{canal.id}/{mensaje_principal.id}"
                embed_anuncio = discord.Embed(
                    title="📢 Actualización de Normas Generales — ¡Nuevo!",
                    description="¡Se han actualizado las normas generales del servidor! Haz clic abajo para conocer las nuevas reglas.",
                    color=0x0057b8
                )
                embed_anuncio.set_thumbnail(url="https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj")
                embed_anuncio.add_field(name="Tipo", value="Normas Generales", inline=True)
                embed_anuncio.add_field(name="Fecha", value=datetime.now().strftime('%d/%m/%Y'), inline=True)
                embed_anuncio.set_footer(text=f"Publicado por Staff VX | VXbot")

                await canal_anuncios.send(embed=embed_anuncio, view=AnuncioView(url_real))
                await registrar_novedad(
                    update_id,
                    "Normas Generales",
                    "Actualización de Normas Generales",
                    "¡Se han actualizado las normas generales del servidor! Haz clic para conocer las nuevas reglas.",
                    url_real,
                    message_id=str(mensaje_principal.id)
                )
                await log_discord(self.bot, "📢 Notificación premium enviada a canal de anuncios.", CANAL_LOGS_ID, "success", "NormasGenerales")
            except Exception as e:
                await log_discord(self.bot, f"❌ Error al notificar actualización: {e}", CANAL_LOGS_ID, "error", "NormasGenerales")

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
