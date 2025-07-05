import discord
from discord.ext import commands
from config import CANAL_FALTAS_ID, CANAL_LOGS_ID, REDIS_URL
import redis
from datetime import datetime, timezone
from utils.logger import log_discord
import asyncio

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
                if mensaje.author == self.bot.user and mensaje.embeds:
                    embed = mensaje.embeds[0]
                    if embed.title and embed.title.startswith("📤 REGISTRO DE "):
                        user_mention = embed.title.split("📤 REGISTRO DE ")[1].strip()
                        registros[user_mention] = mensaje
                elif not mensaje.author.bot:
                    await mensaje.delete()
        except Exception as e:
            await log_discord(self.bot, f"❌ Error al limpiar el canal: {e}")
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
                    user_ids.add(int(key.split(":")[1]))
                except:
                    continue

            total = 0
            bloques = [list(user_ids)[i:i+10] for i in range(0, len(user_ids), 10)]

            for bloque in bloques:
                tareas = []
                for user_id in bloque:
                    tareas.append(self.procesar_usuario(guild, canal, registros, user_id))
                await asyncio.gather(*tareas)
                await asyncio.sleep(3)

            await log_discord(self.bot, f"✅ Panel público actualizado. Total miembros sincronizados: {len(user_ids)}")

        except Exception as e:
            await log_discord(self.bot, f"❌ Error al sincronizar faltas: {e}")

    async def procesar_usuario(self, guild, canal, registros, user_id):
        miembro = guild.get_member(user_id)
        if not miembro:
            miembro = await self.get_user_safe(guild, user_id)
            if not miembro:
                return

        estado = self.obtener_estado(user_id)
        faltas_total, faltas_mes = self.obtener_faltas(user_id)
        embed = self.generar_embed_faltas(miembro, estado, faltas_total, faltas_mes)
        user_mention = miembro.mention

        if user_mention in registros:
            try:
                await registros[user_mention].edit(embed=embed)
            except Exception as e:
                await log_discord(self.bot, f"❌ Error al editar mensaje de {miembro.display_name}: {e}")
        else:
            try:
                await canal.send(embed=embed)
            except discord.errors.HTTPException as e:
                if e.code == 429:
                    await asyncio.sleep(5)
                    await canal.send(embed=embed)
                else:
                    await log_discord(self.bot, f"❌ Error al enviar mensaje de {miembro.display_name}: {e}")

    def obtener_estado(self, user_id):
        estado = self.redis.hget(f"usuario:{user_id}", "estado") or "activo"
        return estado.capitalize()

    def obtener_faltas(self, user_id):
        try:
            total = int(self.redis.hget(f"usuario:{user_id}", "faltas_totales") or 0)
            mes = int(self.redis.hget(f"usuario:{user_id}", "faltas_mes") or 0)
            return total, mes
        except:
            return 0, 0

    def generar_embed_faltas(self, miembro, estado, faltas_total, faltas_mes):
        now = datetime.now(timezone.utc)
        avatar_url = getattr(miembro, "display_avatar", miembro.avatar).url if miembro.avatar else ""

        embed = discord.Embed(
            title=f"📤 REGISTRO DE {miembro.mention}",
            description=(
                f"**Estado actual:** {estado}\n"
                f"**Total de faltas:** {faltas_total}\n"
                f"**Faltas este mes:** {faltas_mes}"
            ),
            color=self.color_estado(estado)
        )
        embed.set_author(name=miembro.display_name, icon_url=avatar_url)
        embed.set_footer(text="Sistema automatizado de reputación pública")
        embed.timestamp = now
        return embed

    def color_estado(self, estado):
        estado = estado.lower()
        colores = {
            "activo": discord.Color.green(),
            "baneado": discord.Color.red(),
            "expulsado": discord.Color.dark_red(),
            "deserción": discord.Color.orange()
        }
        return colores.get(estado, discord.Color.greyple())

    async def get_user_safe(self, guild, user_id):
        try:
            return await guild.fetch_member(user_id)
        except:
            try:
                return await self.bot.fetch_user(user_id)
            except:
                return None

async def setup(bot):
    await bot.add_cog(Faltas(bot))
