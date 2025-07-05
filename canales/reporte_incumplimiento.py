import discord
from discord.ext import commands
from discord import ui
from datetime import datetime, timezone
import redis
from config import CANAL_REPORTE_ID, CANAL_LOGS_ID, REDIS_URL
from utils.logger import log_discord  # <--- Aquí el import del logger
import asyncio

# ---------------------- TEXTOS ----------------------
TITULO_INSTRUCCIONES = "🚨 Reporte de Incumplimiento"
DESCRIPCION_INSTRUCCIONES = (
    "**¿Notas que alguien NO apoyó en X como indican las reglas?**\n\n"
    "• Usa el menú para elegir el motivo del reporte.\n"
    "• Completa los pasos y confirma.\n"
    "• Solo puedes reportar usuarios del servidor.\n\n"
    "**Motivos válidos:**\n"
    "🔸 No apoyó en X (no dio RT, Like o Comentario)\n"
    "🔸 Otro (explica brevemente)\n\n"
    "El proceso es **privado**. Ambas partes serán notificadas por DM y el caso tendrá seguimiento automático.\n"
    "*El abuso de reportes puede ser sancionado.*"
)
FOOTER = "VXbot | Sistema automatizado de reportes"

REPORTE_MOTIVOS = [
    discord.SelectOption(label="No apoyó en 𝕏", description="No cumplió con el apoyo requerido", value="no_apoyo"),
    discord.SelectOption(label="Otro (explica abajo)", description="Otra causa, requiere explicación", value="otro"),
]

# ---------------------- FUNCIONES ----------------------

async def enviar_mensaje_con_reintento(canal, embed):
    # Intentamos enviar el mensaje varias veces en caso de rate limiting
    for intento in range(5):  # Intentar hasta 5 veces
        try:
            await canal.send(embed=embed)
            return  # Si el mensaje se envía correctamente, salimos
        except discord.errors.HTTPException as e:
            if e.code == 429:  # Si el error es rate limiting (429)
                wait_time = 2 ** intento  # Exponential backoff
                await log_discord(self.bot, f"Rate limiting detectado. Esperando {wait_time} segundos...", nivel="warning", titulo="Reporte Incumplimiento")
                await asyncio.sleep(wait_time)  # Esperamos antes de reintentar
            else:
                # Si es otro error, lo registramos y salimos
                await log_discord(self.bot, f"Error inesperado al enviar mensaje: {e}", nivel="error", titulo="Reporte Incumplimiento")
                break

# ---------------------- CLASES ----------------------

class ReporteIncumplimiento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.init_mensaje_instrucciones())

    async def init_mensaje_instrucciones(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_REPORTE_ID)
        if not canal:
            await log_discord(self.bot, "❌ No se encontró el canal de reportes.", nivel="error", titulo="Reporte Incumplimiento")
            return

        hash_key = "reporte_incumplimiento:instrucciones_hash"
        msg_id_key = "reporte_incumplimiento:instrucciones_msg_id"

        embed = discord.Embed(
            title=TITULO_INSTRUCCIONES,
            description=DESCRIPCION_INSTRUCCIONES,
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=FOOTER)

        hash_actual = f"{TITULO_INSTRUCCIONES}|{DESCRIPCION_INSTRUCCIONES}|{FOOTER}"
        hash_guardado = self.redis.get(hash_key)
        msg_id_guardado = self.redis.get(msg_id_key)

        if msg_id_guardado and hash_guardado == hash_actual:
            try:
                mensaje = await canal.fetch_message(int(msg_id_guardado))
                if mensaje and mensaje.embeds and mensaje.embeds[0].description == DESCRIPCION_INSTRUCCIONES:
                    await log_discord(self.bot, "✅ Mensaje de instrucciones ya está actualizado.", nivel="info", titulo="Reporte Incumplimiento")
                    return
            except Exception as e:
                await log_discord(self.bot, f"❌ No se pudo recuperar mensaje anterior: {e}", nivel="warning", titulo="Reporte Incumplimiento")

        msg = None
        if msg_id_guardado:
            try:
                mensaje = await canal.fetch_message(int(msg_id_guardado))
                if mensaje:
                    await mensaje.edit(embed=embed, view=ReporteMenuView(self))
                    msg = mensaje
                else:
                    await log_discord(self.bot, "Mensaje anterior no encontrado, enviando nuevo.", nivel="warning", titulo="Reporte Incumplimiento")
            except Exception as e:
                await log_discord(self.bot, f"❌ No se pudo editar mensaje anterior: {e}", nivel="error", titulo="Reporte Incumplimiento")

        if not msg:
            msg = await canal.send(embed=embed, view=ReporteMenuView(self))
            await msg.pin()

        self.redis.set(hash_key, hash_actual)
        self.redis.set(msg_id_key, str(msg.id))
        await log_discord(self.bot, "✅ Instrucciones del canal de reporte actualizadas y fijadas.", nivel="success", titulo="Reporte Incumplimiento")

# ---------------------- CONTROLES DE REACCIONES Y VIEWS ----------------------

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
            options=REPORTE_MOTIVOS,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        motivo = self.values[0]
        await self.cog.crear_reporte(interaction.user, motivo)

async def setup(bot):
    await bot.add_cog(ReporteIncumplimiento(bot))
