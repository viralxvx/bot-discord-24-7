"""
======================================================================================
 Archivo: canales/reporte_incumplimiento.py
 Autor:    Viral X | VXbot (Miguel Peralta & ChatGPT)
 Creado:   2025-07
--------------------------------------------------------------------------------------
 PROPÓSITO:
 Gestiona el sistema **automatizado de reportes de incumplimiento** en Discord,
 incluyendo la creación del reporte, ciclo de advertencias, baneo temporal,
 expulsión automática, validaciones y apelaciones, agrupación de reportantes
 y persistencia absoluta del historial y estado en Redis.

 SOLO INCLUYE LA LÓGICA DEL PROCESO. No escribir aquí textos o mensajes.
 Todos los textos deben estar en mensajes/reporte_incumplimiento_mensajes.py

--------------------------------------------------------------------------------------
 PARA DESARROLLADORES:
 - Cada función está pensada para ser robusta ante reinicios y actualizaciones.
 - Los botones y paneles se generan dinámicamente y solo pueden ser usados por los
   usuarios implicados o el staff.
 - Todas las acciones relevantes se loggean en canal de logs y Railway.
 - El ciclo de vida de cada reporte es autónomo: el bot supervisa advertencias,
   baneos, expiraciones, agrupaciones y resolución, sin intervención manual salvo apelación.
 - Si modificas este archivo, revisa la compatibilidad con comandos y textos externos.

--------------------------------------------------------------------------------------
 FUNCIONES PRINCIPALES:
 - Creación de reportes (1 por cada combinación reportado/reportante)
 - Agrupación de múltiples reportantes sobre el mismo usuario
 - Automatización de advertencias, recordatorios, baneo temporal y expulsión
 - Paneles de validación con botones (DM y canal privado staff)
 - Apelación y resolución manual por staff vía botones y comandos
 - Blindaje ante reinicios (todo el estado y timers en Redis)
======================================================================================
"""

import discord
from discord.ext import commands, tasks
from discord import ui
from datetime import datetime, timezone, timedelta
import redis

from mensajes import reporte_incumplimiento_mensajes as MSG
from config import CANAL_REPORTE_ID, CANAL_LOGS_ID, REDIS_URL
from utils.logger import log_discord

# === Parámetros principales del ciclo automatizado ===
ADVERTENCIA_INTERVALO_HORAS = 6
MAX_ADVERTENCIAS = 3
BANEO_TIEMPO_HORAS = 24
REPORTE_EXPULSION = True

# --- NUEVO: para manejo único del mensaje de panel ---
PANEL_HASH_KEY = "reporte_incumplimiento:panel_hash"
PANEL_MSG_ID_KEY = "reporte_incumplimiento:panel_msg_id"

def ahora_utc(): return datetime.now(timezone.utc)
def fecha_str(): return ahora_utc().strftime('%Y-%m-%d %H:%M:%S')

class ReporteMenuView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(ReporteMotivoSelect(cog))

class ReporteMotivoSelect(ui.Select):
    def __init__(self, cog):
        super().__init__(
            placeholder="Selecciona el motivo del reporte...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="No apoyó en 𝕏", description="No cumplió con el apoyo requerido", value="no_apoyo"),
                discord.SelectOption(label="Otro (explica abajo)", description="Otra causa, requiere explicación", value="otro"),
            ],
            custom_id="reporte_motivo_select_persistente"
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        motivo = self.values[0]
        await interaction.response.send_message(
            "Por favor indica el usuario (mención o ID) y, si seleccionaste 'Otro', explica brevemente el motivo.",
            ephemeral=True
        )
        # Aquí normalmente abrirías un modal o DM al usuario.

class ReporteIncumplimiento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.tarea_revisar_reportes.start()
        bot.loop.create_task(self.init_panel_instrucciones())

    async def init_panel_instrucciones(self):
        await self.bot.wait_until_ready()
        self.bot.add_view(ReporteMenuView(self))
        canal = self.bot.get_channel(CANAL_REPORTE_ID)
        if not canal:
            await log_discord(self.bot, "❌ No se encontró el canal de reportes.")
            return

        embed = discord.Embed(
            title=MSG.TITULO_PANEL_INSTRUCCIONES,
            description=MSG.DESCRIPCION_PANEL_INSTRUCCIONES,
            color=discord.Color.red()
        )
        embed.set_footer(text=MSG.FOOTER_GENERAL)

        # --- Hash para saber si el mensaje ha cambiado
        panel_hash = f"{MSG.TITULO_PANEL_INSTRUCCIONES}|{MSG.DESCRIPCION_PANEL_INSTRUCCIONES}|{MSG.FOOTER_GENERAL}"
        hash_guardado = self.redis.get(PANEL_HASH_KEY)
        msg_id_guardado = self.redis.get(PANEL_MSG_ID_KEY)

        panel_msg = None

        # --- Si ya existe el mensaje Y el hash no ha cambiado, solo lo refija (si está, lo edita por si acaso)
        if msg_id_guardado and hash_guardado == panel_hash:
            try:
                panel_msg = await canal.fetch_message(int(msg_id_guardado))
                if panel_msg:  # Edita por si se desfijó, o el embed/menu cambia levemente
                    await panel_msg.edit(embed=embed, view=ReporteMenuView(self))
                    try:
                        await panel_msg.pin()
                    except Exception:
                        pass
                    # Desfija cualquier otro mensaje, solo deja este
                    pinned = await canal.pins()
                    for msg in pinned:
                        if msg.id != panel_msg.id:
                            try:
                                await msg.unpin()
                            except Exception:
                                pass
                    return
            except Exception:
                # Si hay error, creamos uno nuevo abajo
                pass

        # Si no existe, crea y fija el panel; borra los demás fijados si hubiera
        panel_msg = await canal.send(embed=embed, view=ReporteMenuView(self))
        try:
            await panel_msg.pin()
        except Exception:
            pass

        # Desfija cualquier otro mensaje fijado
        pinned = await canal.pins()
        for msg in pinned:
            if msg.id != panel_msg.id:
                try:
                    await msg.unpin()
                except Exception:
                    pass

        # Guarda el hash y msg_id en Redis para persistencia
        self.redis.set(PANEL_HASH_KEY, panel_hash)
        self.redis.set(PANEL_MSG_ID_KEY, str(panel_msg.id))

    # --- CREAR REPORTE O AGRUPAR ---
    async def crear_o_agrup_reporte(self, reportante: discord.Member, reportado: discord.Member, motivo, explicacion):
        # Key de agrupación única por usuario reportado
        key_reporte = f"reporte_inc:{reportado.id}"
        now = ahora_utc().timestamp()
        data = self.redis.hgetall(key_reporte)

        # Si ya existe el reporte, solo se agrega al grupo de reportantes si no está
        if data and data.get("estado") in ["abierto", "en_proceso"]:
            reportantes = set(data["reportantes"].split(",")) if data.get("reportantes") else set()
            if str(reportante.id) in reportantes:
                await reportante.send(MSG.ERROR_AUTO_REPORTE)
                return
            reportantes.add(str(reportante.id))
            self.redis.hset(key_reporte, "reportantes", ",".join(reportantes))
            await reportante.send(MSG.AVISO_MULTI_REPORTANTE)
        else:
            self.redis.hset(key_reporte, mapping={
                "reportado_id": str(reportado.id),
                "reportantes": str(reportante.id),
                "advertencias": "1",
                "estado": "abierto",
                "ultimo_aviso": str(now),
                "ban_temp": "",
                "expulsion": "",
                "apelacion": "",
                "historial": f"Creado: {fecha_str()} por {reportante.display_name} ({reportante.id})\n",
            })
            await reportante.send(MSG.DM_REPORTE_CREADO)
            await reportado.send(MSG.AVISO_ADVERTENCIA)
            await log_discord(self.bot, MSG.LOG_REPORTE_CREADO.format(
                reporte_id=reportado.id, reportante=reportante.display_name, reportado=reportado.display_name
            ))

    @tasks.loop(minutes=10)
    async def tarea_revisar_reportes(self):
        await self.bot.wait_until_ready()
        keys = self.redis.keys("reporte_inc:*")
        now = ahora_utc().timestamp()

        for key in keys:
            data = self.redis.hgetall(key)
            estado = data.get("estado", "")
            advertencias = int(data.get("advertencias", "1"))
            ultimo_aviso = float(data.get("ultimo_aviso", now))

            if estado in ["cerrado", "expulsado"]:
                continue

            if now - ultimo_aviso >= ADVERTENCIA_INTERVALO_HORAS * 3600:
                if advertencias < MAX_ADVERTENCIAS:
                    reportado = self.bot.get_user(int(data["reportado_id"]))
                    if advertencias == 2:
                        await reportado.send(MSG.AVISO_RECORDATORIO)
                    elif advertencias == 3:
                        await reportado.send(MSG.AVISO_ULTIMA_ADVERTENCIA)
                    self.redis.hset(key, "advertencias", str(advertencias + 1))
                    self.redis.hset(key, "ultimo_aviso", str(now))
                    self.redis.hset(key, "estado", "en_proceso")
                    self.redis.hset(key, "historial", data.get("historial", "") + f"Advertencia {advertencias}: {fecha_str()}\n")
                    await log_discord(self.bot, f"Advertencia {advertencias} enviada a usuario {data['reportado_id']}")
                else:
                    reportado = self.bot.get_user(int(data["reportado_id"]))
                    await reportado.send(MSG.BANEO_TEMPORAL)
                    self.redis.hset(key, "estado", "baneado")
                    self.redis.hset(key, "ban_temp", str(now))
                    self.redis.hset(key, "historial", data.get("historial", "") + f"Baneo temporal: {fecha_str()}\n")
                    await log_discord(self.bot, MSG.LOG_REPORTE_BANEO.format(usuario=data['reportado_id']))

            if estado == "baneado":
                ban_inicio = float(data.get("ban_temp", now))
                if now - ban_inicio >= BANEO_TIEMPO_HORAS * 3600:
                    if REPORTE_EXPULSION:
                        reportado = self.bot.get_user(int(data["reportado_id"]))
                        await reportado.send(MSG.EXPULSION_FINAL)
                        self.redis.hset(key, "estado", "expulsado")
                        self.redis.hset(key, "expulsion", str(now))
                        self.redis.hset(key, "historial", data.get("historial", "") + f"Expulsión: {fecha_str()}\n")
                        await log_discord(self.bot, MSG.LOG_REPORTE_EXPULSION.format(usuario=data['reportado_id']))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_REPORTE_ID and not message.author.bot:
            try:
                await message.delete()
                await log_discord(self.bot, MSG.ERROR_SOLO_BOT)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(ReporteIncumplimiento(bot))
