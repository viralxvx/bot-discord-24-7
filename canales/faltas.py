import os
from discord.ext import commands
import discord
import aiohttp
import asyncio
import redis
from datetime import datetime, timedelta, timezone
from aiolimiter import AsyncLimiter
from discord.errors import HTTPException
from config import CANAL_FALTAS_ID, REDIS_URL
from utils.logger import log_discord
from mensajes.viral_texto import (
    TITULO_SIN_LIKE_DM, DESCRIPCION_SIN_LIKE_DM,
    TITULO_APOYO_9_DM, DESCRIPCION_APOYO_9_DM,
    TITULO_INTERVALO_DM, DESCRIPCION_INTERVALO_DM,
)

# --- FUNCIONES INTERNAS ---

def obtener_estado(redis_client, user_id):
    estado = redis_client.hget(f"usuario:{user_id}", "estado")
    if not estado:
        return "Activo"
    estado = estado.lower()
    return {
        "baneado": "Baneado",
        "expulsado": "Expulsado",
        "desercion": "Deserción"
    }.get(estado, "Activo")

def obtener_faltas(redis_client, user_id):
    try:
        total = int(redis_client.hget(f"usuario:{user_id}", "faltas_totales") or 0)
        mes = int(redis_client.hget(f"usuario:{user_id}", "faltas_mes") or 0)
        return total, mes
    except:
        return 0, 0

def generar_hash_datos(estado, faltas_total, faltas_mes):
    return f"{estado}:{faltas_total}:{faltas_mes}"

def siguiente_bloqueo(total_faltas):
    if total_faltas == 1:
        return 0  # solo aviso DM
    elif total_faltas == 2:
        return 24 * 3600  # 24 horas
    elif total_faltas == 3:
        return 7 * 24 * 3600  # 1 semana
    return 0

async def enviar_aviso_dm(bot, user_id, motivo):
    # Selecciona el mensaje DM según el motivo
    try:
        user = await bot.fetch_user(int(user_id))
        if not user:
            return
        if motivo == "No validar publicación con 👍 en 2 minutos":
            embed = discord.Embed(
                title=TITULO_SIN_LIKE_DM,
                description=DESCRIPCION_SIN_LIKE_DM,
                color=discord.Color.orange()
            )
            await user.send(embed=embed)
        elif motivo == "No apoyar publicaciones anteriores":
            embed = discord.Embed(
                title=TITULO_APOYO_9_DM,
                description=DESCRIPCION_APOYO_9_DM,
                color=discord.Color.orange()
            )
            await user.send(embed=embed)
        elif motivo == "No respetar intervalo de publicaciones":
            embed = discord.Embed(
                title=TITULO_INTERVALO_DM,
                description=DESCRIPCION_INTERVALO_DM,
                color=discord.Color.orange()
            )
            await user.send(embed=embed)
        else:
            await user.send(f"Has recibido una falta automática por: {motivo}")
    except Exception:
        pass

# --- FUNCIÓN GLOBAL DE REGISTRO DE FALTA ---

async def registrar_falta(user_id, motivo):
    """
    Esta función debe ser llamada por cualquier módulo que detecte una infracción
    """
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    total = int(redis_client.hincrby(f"usuario:{user_id}", "faltas_totales", 1))
    mes = int(redis_client.hincrby(f"usuario:{user_id}", "faltas_mes", 1))
    now = datetime.now(timezone.utc)
    redis_client.hset(f"usuario:{user_id}", "ultima_falta", str(now.timestamp()))
    # Bloqueos automáticos por faltas
    bloqueo = siguiente_bloqueo(total)
    if bloqueo > 0:
        redis_client.set(f"go_viral:bloqueado:{user_id}", "1", ex=bloqueo)
    # Logs y avisos
    await log_discord(None, f"Usuario {user_id} recibió falta por: {motivo} (Total: {total}, Mes: {mes})", "warning", scope="faltas")
    # Notificación DM (opcional según tipo de falta)
    # (No hay acceso directo a bot, por eso el DM se hace solo desde el cog abajo)
    return total, bloqueo

# --- PANEL FALTAS ---

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.limiter = AsyncLimiter(40, 1)  # 40 req/seg
        self.webhook_url = os.getenv("WEB_HOOKS_FALTAS")
        bot.loop.create_task(self.inicializar_panel_faltas())

    async def inicializar_panel_faltas(self):
        await self.bot.wait_until_ready()
        await log_discord(self.bot, "Iniciando módulo de faltas...")

        canal = self.bot.get_channel(CANAL_FALTAS_ID)
        if not canal:
            await log_discord(self.bot, "❌ Error: no se encontró el canal de faltas.")
            return

        await log_discord(self.bot, "🔄 Sincronizando registros públicos de usuarios...")
        try:
            guild = canal.guild
            user_ids = set()
            async for member in guild.fetch_members(limit=None):
                if not member.bot:
                    user_ids.add(member.id)

            for key in self.redis.scan_iter("usuario:*"):
                try:
                    user_id = int(key.split(":")[1])
                    user_ids.add(user_id)
                except:
                    continue

            total = 0
            bloques = [list(user_ids)[i:i + 5] for i in range(0, len(user_ids), 5)]
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(self.webhook_url, session=session)
                for bloque in bloques:
                    for user_id in bloque:
                        async with self.limiter:
                            miembro = guild.get_member(user_id)
                            if not miembro:
                                continue

                            estado = obtener_estado(self.redis, user_id)
                            faltas_total, faltas_mes = obtener_faltas(self.redis, user_id)
                            embed = self.generar_embed_faltas(miembro, estado, faltas_total, faltas_mes)
                            current_hash = generar_hash_datos(estado, faltas_total, faltas_mes)

                            panel_key = f"panel:{user_id}"
                            hash_key = f"hash:{user_id}"
                            mensaje_id = self.redis.get(panel_key)
                            previous_hash = self.redis.get(hash_key)

                            if current_hash == previous_hash:
                                continue

                            try:
                                if mensaje_id:
                                    await webhook.edit_message(int(mensaje_id), embed=embed)
                                else:
                                    mensaje = await webhook.send(embed=embed, wait=True)
                                    self.redis.set(panel_key, mensaje.id)
                                self.redis.set(hash_key, current_hash)
                                total += 1
                            except HTTPException as e:
                                if e.status == 429:
                                    retry_after = float(e.response.headers.get("Retry-After", 1))
                                    await log_discord(self.bot, f"⚠️ Rate limit alcanzado, esperando {retry_after}s")
                                    await asyncio.sleep(retry_after)
                                    try:
                                        if mensaje_id:
                                            await webhook.edit_message(int(mensaje_id), embed=embed)
                                        else:
                                            mensaje = await webhook.send(embed=embed, wait=True)
                                            self.redis.set(panel_key, mensaje.id)
                                        self.redis.set(hash_key, current_hash)
                                    except Exception as retry_error:
                                        await log_discord(self.bot, f"❌ Error tras reintento con {user_id}: {retry_error}")
                                else:
                                    await log_discord(self.bot, f"❌ Error con {user_id}: {e}")
                    await asyncio.sleep(1)

            await log_discord(self.bot, f"✅ Panel público actualizado. Total usuarios verificados: {len(user_ids)}. Actualizados: {total}", status="Activo")            
        except Exception as e:
            await log_discord(self.bot, f"❌ Error al sincronizar faltas: {e}")

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
        embed.set_footer(text="Sistema automatizado", icon_url=avatar_url)
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
