import discord
from discord.ext import commands
from config import CANAL_FALTAS_ID, CANAL_LOGS_ID, REDIS_URL
import redis
from datetime import datetime, timezone
from utils.logger import log_discord  # <--- Aquí el import del logger
import asyncio

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

async def enviar_mensaje_con_reintento(canal, embed):
    # Intentamos enviar el mensaje varias veces en caso de rate limiting
    for intento in range(5):  # Intentar hasta 5 veces
        try:
            await canal.send(embed=embed)
            return  # Si el mensaje se envía correctamente, salimos
        except discord.errors.HTTPException as e:
            if e.code == 429:  # Si el error es rate limiting (429)
                wait_time = 2 ** intento  # Exponential backoff
                await log_discord(self.bot, f"Rate limiting detectado. Esperando {wait_time} segundos...")
                await asyncio.sleep(wait_time)  # Esperamos antes de reintentar
            else:
                # Si es otro error, lo registramos y salimos
                await log_discord(self.bot, f"Error inesperado al enviar mensaje: {e}")
                break

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.inicializar_panel_faltas())

    async def inicializar_panel_faltas(self):
        await self.bot.wait_until_ready()
        await log_discord(self.bot, "Iniciando módulo de faltas...")  # Eliminado 'titulo'

        canal = self.bot.get_channel(CANAL_FALTAS_ID)
        if not canal:
            await log_discord(self.bot, "❌ Error: no se encontró el canal de faltas.")  # Eliminado 'titulo'
            return

        await log_discord(self.bot, "Cargando mensajes existentes del canal #📤faltas...")  # Eliminado 'titulo'
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
            await log_discord(self.bot, f"❌ Error al leer mensajes del canal: {e}")  # Eliminado 'titulo'
            return

        await log_discord(self.bot, "Sincronizando mensajes por miembro...")  # Eliminado 'titulo'

        try:
            guild = canal.guild
            user_ids = set()

            # 1. Todos los miembros actuales
            for miembro in guild.members:
                if miembro.bot:
                    continue
                user_ids.add(miembro.id)

            # 2. Usuarios con estado en Redis (baneados, expulsados, deserción)
            keys = self.redis.keys("usuario:*")
            for key in keys:
                try:
                    user_id = int(key.split(":")[1])
                    user_ids.add(user_id)
                except:
                    continue

            total = 0
            for user_id in user_ids:
                miembro = guild.get_member(user_id)
                if not miembro:
                    miembro = await self.get_user_safe(guild, user_id)
                    if not miembro:
                        continue

                estado = obtener_estado(self.redis, user_id)
                faltas_total, faltas_mes = obtener_faltas(self.redis, user_id)
                embed = self.generar_embed_faltas(miembro, estado, faltas_total, faltas_mes)

                user_mention = miembro.mention
                if user_mention in registros:
                    try:
                        await registros[user_mention].edit(embed=embed)
                        await asyncio.sleep(1)  # Espera 1 segundo
                    except Exception as e:
                        await log_discord(self.bot, f"❌ Error al editar mensaje de {miembro.display_name}: {e}")  # Eliminado 'titulo'
                else:
                    await enviar_mensaje_con_reintento(canal, embed)  # Usamos la nueva función con reintentos
                    total += 1

            await log_discord(self.bot, f"✅ Panel público actualizado. Total miembros sincronizados: {total}")  # Eliminado 'titulo'

        except Exception as e:
            await log_discord(self.bot, f"❌ Error al sincronizar faltas: {e}")  # Eliminado 'titulo'

    async def get_user_safe(self, guild, user_id):
        try:
            user = await guild.fetch_member(user_id)
        except:
            try:
                user = await self.bot.fetch_user(user_id)
            except:
                user = None
        return user

    def generar_embed_faltas(self, miembro, estado, faltas_total, faltas_mes):
        now = datetime.now(timezone.utc)
        avatar_url = ""
        if hasattr(miembro, "display_avatar"):
            try:
                avatar_url = miembro.display_avatar.url
            except:
                avatar_url = ""
        elif hasattr(miembro, "avatar") and miembro.avatar:
            avatar_url = miembro.avatar.url
        else:
            avatar_url = ""

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
        if estado == "activo":
            return discord.Color.green()
        elif estado == "baneado":
            return discord.Color.red()
        elif estado == "expulsado":
            return discord.Color.dark_red()
        elif estado == "deserción":
            return discord.Color.orange()
        else:
            return discord.Color.greyple()

async def setup(bot):
    await bot.add_cog(Faltas(bot))
