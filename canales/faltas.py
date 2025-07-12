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
import json

# --- FUNCIONES INTERNAS ---

def obtener_estado(redis_client, user_id):
    estado = redis_client.hget(f"usuario:{user_id}", "estado")
    if not estado:
        return "Activo"
    return estado.capitalize()

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

async def enviar_aviso_dm(bot, user_id, motivo, embed=None):
    try:
        user = await bot.fetch_user(int(user_id))
        if embed:
            await user.send(embed=embed)
        else:
            await user.send(f"Has recibido una falta automática por: {motivo}")
    except Exception:
        pass

# --- REGISTRO GLOBAL DE FALTA ---

async def registrar_falta(bot, user_id, motivo, canal=None, moderador=None):
    """
    Registrar una falta: suma contadores, guarda historial y actualiza panel.
    """
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    now = datetime.now(timezone.utc)
    total = int(redis_client.hincrby(f"usuario:{user_id}", "faltas_totales", 1))
    mes = int(redis_client.hincrby(f"usuario:{user_id}", "faltas_mes", 1))
    redis_client.hset(f"usuario:{user_id}", "ultima_falta", str(now.timestamp()))

    # Guardar historial
    entry = {
        "fecha": now.strftime("%Y-%m-%d %H:%M"),
        "motivo": motivo,
        "canal": canal or "-",
        "moderador": moderador or "Sistema"
    }
    redis_client.rpush(f"faltas_historial:{user_id}", json.dumps(entry))

    # Bloqueos automáticos por faltas
    bloqueo = siguiente_bloqueo(total)
    if bloqueo > 0:
        redis_client.set(f"go_viral:bloqueado:{user_id}", "1", ex=bloqueo)

    # Logs y avisos
    await log_discord(bot, f"Usuario {user_id} recibió falta por: {motivo} (Total: {total}, Mes: {mes})", "warning", scope="faltas")

    # Notificación DM básica (puedes personalizar para cada motivo con embed si prefieres)
    await enviar_aviso_dm(bot, user_id, motivo)

    # Actualiza el panel embed
    miembro = None
    for guild in bot.guilds:
        miembro = guild.get_member(int(user_id))
        if miembro:
            break
    if miembro:
        await actualizar_panel_faltas(bot, miembro)

    return total, bloqueo

# --- PANEL FALTAS ---

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.limiter = AsyncLimiter(40, 1)  # 40 req/seg
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

            bloques = [list(user_ids)[i:i + 5] for i in range(0, len(user_ids), 5)]
            async with aiohttp.ClientSession() as session:
                for bloque in bloques:
                    for user_id in bloque:
                        async with self.limiter:
                            miembro = guild.get_member(user_id)
                            if not miembro:
                                continue
                            await actualizar_panel_faltas(self.bot, miembro)
                    await asyncio.sleep(1)
            await log_discord(self.bot, f"✅ Panel público actualizado. Total usuarios: {len(user_ids)}", status="Activo")
        except Exception as e:
            await log_discord(self.bot, f"❌ Error al sincronizar faltas: {e}")

async def actualizar_panel_faltas(bot, miembro):
    """
    Genera y actualiza el embed del panel de reputación de un usuario.
    Esto debe centralizarse y luego ampliarse en el siguiente archivo para más detalles visuales.
    """
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    user_id = miembro.id
    canal = bot.get_channel(CANAL_FALTAS_ID)

    # --- DATOS PARA EL PANEL ---
    estado = obtener_estado(redis_client, user_id)
    faltas_total, faltas_mes = obtener_faltas(redis_client, user_id)
    ultima_falta_ts = redis_client.hget(f"usuario:{user_id}", "ultima_falta")
    ultima_falta_dt = datetime.fromtimestamp(float(ultima_falta_ts), timezone.utc) if ultima_falta_ts else None
    prorroga_key = f"inactividad:prorroga:{user_id}"
    prorroga_activa = redis_client.get(prorroga_key)
    prorroga_text = "-"
    if prorroga_activa:
        prorroga_dt = datetime.fromisoformat(prorroga_activa)
        prorroga_text = f"Hasta <t:{int(prorroga_dt.timestamp())}:R>"
    last_publi = redis_client.get(f"inactividad:{user_id}")
    last_publi_dt = datetime.fromisoformat(last_publi) if last_publi else None

    # Historial reciente (últimas 3 faltas)
    faltas_hist = redis_client.lrange(f"faltas_historial:{user_id}", -3, -1)
    if faltas_hist:
        ultimas_faltas = []
        for f in faltas_hist:
            entry = json.loads(f)
            ultimas_faltas.append(
                f"`{entry['fecha']}`: {entry['motivo']} ({entry['canal']}) — {entry['moderador']}"
            )
        faltas_text = "\n".join(ultimas_faltas)
    else:
        faltas_text = "*Sin faltas recientes*"

    # Visual profesional
    embed = discord.Embed(
        title=f"📤 REGISTRO DE {miembro.display_name} ({miembro})",
        color=discord.Color.green() if estado.lower() == "activo" else discord.Color.red()
    )
    avatar_url = getattr(getattr(miembro, "display_avatar", None), "url", "") or getattr(getattr(miembro, "avatar", None), "url", "")
    embed.set_thumbnail(url=avatar_url)
    embed.add_field(name="Estado actual", value=estado, inline=True)
    embed.add_field(name="Faltas totales", value=faltas_total, inline=True)
    embed.add_field(name="Faltas este mes", value=faltas_mes, inline=True)
    if ultima_falta_dt:
        embed.add_field(name="Última falta", value=f"<t:{int(ultima_falta_dt.timestamp())}:R>", inline=True)
    if last_publi_dt:
        embed.add_field(name="Última publicación", value=f"<t:{int(last_publi_dt.timestamp())}:R>", inline=True)
    embed.add_field(name="Prórroga activa", value=prorroga_text, inline=True)
    embed.add_field(name="Historial reciente", value=faltas_text, inline=False)
    embed.set_footer(text="Sistema automatizado de reputación pública")
    embed.timestamp = datetime.now(timezone.utc)

    # --- ACTUALIZAR/CREAR PANEL EN EL CANAL ---
    panel_key = f"panel:{user_id}"
    hash_key = f"hash:{user_id}"
    current_hash = generar_hash_datos(estado, faltas_total, faltas_mes)
    mensaje_id = redis_client.get(panel_key)
    previous_hash = redis_client.get(hash_key)

    async with aiohttp.ClientSession() as session:
        webhook_url = os.getenv("WEB_HOOKS_FALTAS")
        if webhook_url:
            webhook = discord.Webhook.from_url(webhook_url, session=session)
            try:
                if mensaje_id and current_hash != previous_hash:
                    await webhook.edit_message(int(mensaje_id), embed=embed)
                    redis_client.set(hash_key, current_hash)
                elif not mensaje_id:
                    msg = await webhook.send(embed=embed, wait=True)
                    redis_client.set(panel_key, msg.id)
                    redis_client.set(hash_key, current_hash)
            except Exception as e:
                await log_discord(bot, f"❌ Error actualizando panel de {miembro.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(Faltas(bot))
