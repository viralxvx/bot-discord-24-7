import discord
from discord.ext import commands
from config import CANAL_FALTAS_ID, CANAL_LOGS_ID, REDIS_URL
import redis
from datetime import datetime, timezone
from utils.logger import log_discord
import asyncio
import random

def obtener_estado(redis, user_id):
    estado = redis.hget(f"usuario:{user_id}", "estado")
    if not estado:
        return "Activo"
    estado = estado.lower()
    if estado == "baneado":
        return "Baneado"
    elif estado == "expulsado":
        return "Expulsado"
    elif estado == "desercion":
        return "Deserción"
    else:
        return "Activo"

def obtener_faltas(redis, user_id):
    try:
        total = int(redis.hget(f"usuario:{user_id}", "faltas_totales") or 0)
        mes = int(redis.hget(f"usuario:{user_id}", "faltas_mes") or 0)
        return total, mes
    except:
        return 0, 0

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.inicializar_panel_faltas())

    async def inicializar_panel_faltas(self):
        await self.bot.wait_until_ready()
        await log_discord(self.bot, "Iniciando módulo de faltas...")
        canal = self.bot.get_channel(CANAL_FALTAS_ID)
        if not canal:
            await log_discord(self.bot, "❌ Error: no se encontró el canal de faltas.")
            return

        await log_discord(self.bot, "🧹 Cargando mensajes existentes del canal #📤faltas...")
        registros = {}

        try:
            async for mensaje in canal.history(limit=None):
                if mensaje.author.bot and mensaje.embeds:
                    embed = mensaje.embeds[0]
                    titulo = embed.title
                    if titulo and titulo.startswith("📤 REGISTRO DE "):
                        user_mention = titulo.split("📤 REGISTRO DE ")[1].strip()
                        registros[user_mention] = mensaje
        except Exception as e:
            await log_discord(self.bot, f"❌ Error al leer mensajes del canal: {e}")
            return

        await log_discord(self.bot, "🔄 Sincronizando registros públicos de usuarios...")

        try:
            guild = canal.guild
            user_ids = set()
            for miembro in guild.members:
                if not miembro.bot:
                    user_ids.add(miembro.id)

            keys = self.redis.keys("usuario:*")
            for key in keys:
                try:
                    user_id = int(key.split(":")[1])
                    user_ids.add(user_id)
                except:
                    continue

            total = 0
            bloques = [list(user_ids)[i:i+5] for i in range(0, len(user_ids), 5)]

            for bloque in bloques:
                for user_id in bloque:
                    miembro = guild.get_member(user_id)
                    if not miembro:
                        miembro = await self.get_user_safe(guild, user_id)
                        if not miembro:
                            continue

                    estado = obtener_estado(self.redis, user_id)
                    faltas_total, faltas_mes = obtener_faltas(self.redis, user_id)
                    embed_nuevo = self.generar_embed_faltas(miembro, estado, faltas_total, faltas_mes)
                    user_mention = miembro.mention

                    mensaje_existente = registros.get(user_mention)
                    if mensaje_existente:
                        embed_viejo = mensaje_existente.embeds[0].to_dict()
                        embed_nuevo_dict = embed_nuevo.to_dict()
                        if embed_viejo != embed_nuevo_dict:
                            try:
                                await mensaje_existente.edit(embed=embed_nuevo)
                                total += 1
                                await asyncio.sleep(random.uniform(1.5, 2.5))
                            except Exception as e:
                                await log_discord(self.bot, f"❌ Error al editar mensaje de {miembro.display_name}: {e}")
                    else:
                        try:
                            await canal.send(embed=embed_nuevo)
                            total += 1
                            await asyncio.sleep(random.uniform(1.5, 2.5))
                        except Exception as e:
                            await log_discord(self.bot, f"❌ Error al enviar mensaje de {miembro.display_name}: {e}")
                await asyncio.sleep(3)

            await log_discord(self.bot, f"✅ Panel público actualizado. Total miembros sincronizados: {total}")

        except Exception as e:
            await log_discord(self.bot, f"❌ Error al sincronizar faltas: {e}")

    async def get_user_safe(self, guild, user_id):
        try:
            return await guild.fetch_member(user_id)
        except:
            try:
                return await self.bot.fetch_user(user_id)
            except:
                return None

    def generar_embed_faltas(self, miembro, estado, faltas_total, faltas_mes):
        now = datetime.now(timezone.utc)
        avatar_url = getattr(getattr(miembro, "display_avatar", None), "url", "") or getattr(getattr(miembro, "avatar", None), "url", "")
        embed = discord.Embed(
            title=f"📤 REGISTRO DE {miembro.mention}",
            description=(
                f"**Estado actual:** {estado}\n"
                f"**Total de faltas:** {faltas_total}\n"
                f"**Faltas este mes:** {faltas_mes}"
            ),
            color=self.color_estado(estado)
        )
        embed.set_author(name=getattr(miembro, 'display_name', 'Miembro'), icon_url=avatar_url)
        embed.set_footer(text="Sistema automatizado de reputación pública", icon_url=avatar_url)
        embed.timestamp = now
        return embed

    def color_estado(self, estado):
        estado = estado.lower()
        return {
            "activo": discord.Color.green(),
            "baneado": discord.Color.red(),
            "expulsado": discord.Color.dark_red(),
            "deserción": discord.Color.orange()
        }.get(estado, discord.Color.greyple())

async def setup(bot):
    await bot.add_cog(Faltas(bot))
