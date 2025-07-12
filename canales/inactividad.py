import discord
from discord.ext import commands, tasks
import redis
from datetime import datetime, timedelta, timezone
from config import CANAL_OBJETIVO_ID, CANAL_FALTAS_ID, CANAL_LOGS_ID, REDIS_URL
from mensajes.inactividad_texto import AVISO_BANEO, AVISO_EXPULSION, PRORROGA_CONCEDIDA
from utils.logger import log_discord
import json

DIAS_LIMITE_INACTIVIDAD = 3  # Para miembros que ya han publicado
DIAS_BANEO_INICIAL = 3       # Baneo inicial para quien nunca publicó
DIAS_BANEO_REINCIDENCIA = 7  # Baneo tras reincidencia
NUM_ADVERTENCIAS = 3         # Advertencias antes de ban o expulsión

class Inactividad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.registrar_actividad())
        self.verificar_inactivos.start()

    async def registrar_actividad(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_OBJETIVO_ID)
        if not canal:
            await log_discord(self.bot, "❌ [INACTIVIDAD] No se encontró el canal 🧵go-viral.", "error", "Inactividad")
            return

        ultimos_mensajes = {}
        try:
            async for mensaje in canal.history(limit=None, oldest_first=False):
                autor = mensaje.author
                if autor.bot:
                    continue
                user_id = str(autor.id)
                if user_id not in ultimos_mensajes or mensaje.created_at > ultimos_mensajes[user_id]:
                    ultimos_mensajes[user_id] = mensaje.created_at
            # Actualiza la última publicación en Redis
            for user_id, fecha in ultimos_mensajes.items():
                fecha_iso = fecha.astimezone(timezone.utc).isoformat()
                self.redis.set(f"inactividad:{user_id}", fecha_iso)
            await log_discord(self.bot, f"✅ [INACTIVIDAD] Registro de actividad inicial completado. Usuarios únicos: {len(ultimos_mensajes)}", "success", "Inactividad")
        except Exception as e:
            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error escaneando mensajes: {e}", "error", "Inactividad")

    @tasks.loop(hours=6)
    async def verificar_inactivos(self):
        await self.bot.wait_until_ready()
        ahora = datetime.now(timezone.utc)

        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue

                user_id = str(member.id)
                estado = self.redis.hget(f"usuario:{user_id}", "estado") or "activo"

                # No operar sobre expulsados, baneados, deserción o prórrogas activas
                if estado in ["expulsado", "desercion", "baneado"]:
                    continue
                if self.redis.get(f"inactividad:prorroga:{user_id}"):
                    continue

                # ¿El usuario ha publicado alguna vez?
                last_post_iso = self.redis.get(f"inactividad:{user_id}")
                advertencias = int(self.redis.get(f"inactividad:advertencias:{user_id}") or 0)
                reincidencias = int(self.redis.get(f"inactividad:reincidencia:{user_id}") or 0)

                if not last_post_iso:
                    # Usuario nunca ha publicado
                    if advertencias < NUM_ADVERTENCIAS:
                        # Enviar advertencia
                        await self.enviar_advertencia(member, advertencias+1)
                        self.redis.incr(f"inactividad:advertencias:{user_id}")
                        self.registrar_inactividad_historial(user_id, "advertencia", f"Advertencia #{advertencias+1}: No ha publicado en go-viral")
                        await self.actualizar_panel_faltas(member)
                        continue
                    else:
                        # Baneo inicial
                        if reincidencias == 0 and estado != "baneado":
                            await self.banear_por_inactividad(member, "Nunca publicó tras 3 advertencias", DIAS_BANEO_INICIAL)
                            self.redis.set(f"inactividad:reincidencia:{user_id}", 1)
                            self.registrar_inactividad_historial(user_id, "baneo", f"Baneado por nunca publicar tras advertencias")
                            await self.actualizar_panel_faltas(member)
                        # Si reincide después de ban inicial, expulsar
                        elif reincidencias >= 1 and estado != "expulsado":
                            await self.expulsar_por_inactividad(member, "Nunca publicó tras baneo y 3 nuevas advertencias")
                            self.redis.set(f"inactividad:reincidencia:{user_id}", reincidencias+1)
                            self.registrar_inactividad_historial(user_id, "expulsion", f"Expulsado por nunca publicar tras baneo/reincidencia")
                            await self.actualizar_panel_faltas(member)
                        continue
                else:
                    # Usuario sí ha publicado alguna vez
                    try:
                        last_post = datetime.fromisoformat(last_post_iso)
                    except Exception:
                        continue
                    dias_inactivo = (ahora - last_post).days
                    # Si ya pasó el límite y no tiene prórroga ni está baneado
                    if dias_inactivo >= DIAS_LIMITE_INACTIVIDAD:
                        if reincidencias == 0 and estado != "baneado":
                            await self.banear_por_inactividad(member, f"Inactividad > {DIAS_LIMITE_INACTIVIDAD} días", DIAS_BANEO_REINCIDENCIA)
                            self.redis.set(f"inactividad:reincidencia:{user_id}", 1)
                            self.registrar_inactividad_historial(user_id, "baneo", f"Baneado por inactividad tras {dias_inactivo} días sin publicar")
                            await self.actualizar_panel_faltas(member)
                        elif reincidencias >= 1 and estado != "expulsado":
                            await self.expulsar_por_inactividad(member, f"Inactividad reincidente > {DIAS_LIMITE_INACTIVIDAD} días")
                            self.redis.set(f"inactividad:reincidencia:{user_id}", reincidencias+1)
                            self.registrar_inactividad_historial(user_id, "expulsion", f"Expulsado por reincidencia en inactividad")
                            await self.actualizar_panel_faltas(member)
                        continue
                    else:
                        # Usuario activo, limpiar advertencias previas si las había
                        if advertencias > 0:
                            self.redis.delete(f"inactividad:advertencias:{user_id}")

    async def enviar_advertencia(self, member, advert_num):
        try:
            msg = f"🚨 **ADVERTENCIA {advert_num}/3**\n\nNo has publicado en el canal 🧵go-viral. Debes presentarte y publicar para evitar sanción automática.\n\nPublica cuanto antes para no ser expulsado temporalmente."
            await member.send(msg)
            await log_discord(self.bot, f"[INACTIVIDAD] Advertencia {advert_num} enviada a {member.display_name} ({member.id})", "info", "Inactividad")
        except Exception as e:
            await log_discord(self.bot, f"[INACTIVIDAD] Error enviando advertencia DM a {member.display_name}: {e}", "warning", "Inactividad")

    async def banear_por_inactividad(self, member, motivo, dias_baneo):
        guild = member.guild
        try:
            await guild.ban(member, reason=motivo, delete_message_days=0)
            self.redis.hset(f"usuario:{member.id}", "estado", "baneado")
            ahora = datetime.now(timezone.utc)
            self.redis.set(f"inactividad:ban:{member.id}", ahora.isoformat())
            self.redis.expire(f"inactividad:ban:{member.id}", dias_baneo*24*60*60)
            try:
                await member.send(AVISO_BANEO)
            except Exception:
                pass
            await log_discord(self.bot, f"⛔ [INACTIVIDAD] Usuario {member.display_name} ({member.id}) baneado por inactividad: {motivo}", "warning", "Inactividad")
            canal_faltas = self.bot.get_channel(CANAL_FALTAS_ID)
            if canal_faltas:
                await canal_faltas.send(f"⛔ Usuario baneado automáticamente por inactividad: {member.mention}")
        except Exception as e:
            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error baneando a {member.display_name}: {e}", "error", "Inactividad")

    async def expulsar_por_inactividad(self, member, motivo):
        guild = member.guild
        try:
            await guild.kick(member, reason=motivo)
            self.redis.hset(f"usuario:{member.id}", "estado", "expulsado")
            self.redis.set(f"inactividad:expulsado:{member.id}", "1")
            try:
                await member.send(AVISO_EXPULSION)
            except Exception:
                pass
            await log_discord(self.bot, f"🚫 [INACTIVIDAD] Usuario {member.display_name} ({member.id}) EXPULSADO por inactividad: {motivo}", "error", "Inactividad")
            canal_faltas = self.bot.get_channel(CANAL_FALTAS_ID)
            if canal_faltas:
                await canal_faltas.send(f"🚫 Usuario EXPULSADO permanentemente por reincidencia de inactividad: {member.display_name}")
        except Exception as e:
            await log_discord(self.bot, f"❌ [INACTIVIDAD] Error expulsando a {member.display_name}: {e}", "error", "Inactividad")

    def registrar_inactividad_historial(self, user_id, accion, detalle):
        now = datetime.now(timezone.utc)
        entry = {
            "fecha": now.strftime("%Y-%m-%d %H:%M"),
            "accion": accion,
            "detalle": detalle
        }
        self.redis.rpush(f"inactividad_historial:{user_id}", json.dumps(entry))

    async def actualizar_panel_faltas(self, member):
        # IMPORTANTE: Aquí debes llamar a la función que actualiza el panel embed del usuario en el canal de faltas.
        # Por ahora, solo ejemplo de log:
        await log_discord(self.bot, f"[PANEL] Actualización del panel de faltas para {member.display_name} ({member.id})", "info", "Panel")

# =============== LISTENERS UNIVERSALES DE ESTADO ===============

class EstadoMiembros(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.redis.hset(f"usuario:{user.id}", "estado", "baneado")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        self.redis.hset(f"usuario:{user.id}", "estado", "activo")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        expulsado = self.redis.get(f"inactividad:expulsado:{member.id}")
        if expulsado == "1":
            self.redis.hset(f"usuario:{member.id}", "estado", "expulsado")
        else:
            self.redis.hset(f"usuario:{member.id}", "estado", "desercion")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.redis.hset(f"usuario:{member.id}", "estado", "activo")
        # Resetear advertencias e historial si vuelve a entrar:
        self.redis.delete(f"inactividad:advertencias:{member.id}")
        self.redis.delete(f"inactividad:reincidencia:{member.id}")
        self.redis.delete(f"inactividad:ban:{member.id}")
        self.redis.delete(f"inactividad:expulsado:{member.id}")
        # Aquí podrías también volver a crear su panel en faltas, si aplica

async def setup(bot):
    await bot.add_cog(Inactividad(bot))
    await bot.add_cog(EstadoMiembros(bot))
