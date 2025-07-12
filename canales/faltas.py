import os
from discord.ext import commands
import discord
import aiohttp
import asyncio
import redis
from datetime import datetime, timezone
from aiolimiter import AsyncLimiter
from discord.errors import HTTPException
from config import CANAL_FALTAS_ID, REDIS_URL
from utils.logger import log_discord
from utils.panel_embed import actualizar_panel_faltas
from mensajes.viral_texto import (
    TITULO_SIN_LIKE_DM, DESCRIPCION_SIN_LIKE_DM,
    TITULO_APOYO_9_DM, DESCRIPCION_APOYO_9_DM,
    TITULO_INTERVALO_DM, DESCRIPCION_INTERVALO_DM,
)

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
            for user_id in user_ids:
                miembro = guild.get_member(user_id)
                if not miembro or miembro.bot:
                    continue
                try:
                    await actualizar_panel_faltas(self.bot, miembro)
                    total += 1
                except Exception as e:
                    print(f"❌ Error sincronizando panel premium de {miembro.display_name}: {e}")
                await asyncio.sleep(0.5)

            await log_discord(self.bot, f"✅ Panel público actualizado. Total usuarios verificados: {len(user_ids)}. Actualizados: {total}", status="Activo")            
        except Exception as e:
            await log_discord(self.bot, f"❌ Error al sincronizar faltas: {e}")

    # --- LISTENER: Recrea panel si alguien lo borra manualmente ---
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id == CANAL_FALTAS_ID:
            redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            for key in redis_client.scan_iter("panel:*"):
                user_id = key.split(":")[1]
                if redis_client.get(key) == str(message.id):
                    for guild in self.bot.guilds:
                        miembro = guild.get_member(int(user_id))
                        if miembro and not miembro.bot:
                            print(f"[REALTIME] Panel de {miembro.display_name} fue borrado, recreando ahora.")
                            await actualizar_panel_faltas(self.bot, miembro)
                    # Limpia Redis del panel borrado (por si acaso)
                    redis_client.delete(key)
                    redis_client.delete(f"hash:{user_id}")

async def setup(bot):
    await bot.add_cog(Faltas(bot))
