import discord
from discord.ext import commands
from discord import ui
from datetime import datetime, timezone
import redis
import asyncio
import logging
from config import CANAL_REPORTE, CANAL_LOGS, REDIS_URL

# ----- Configura tu logger para Railway y consola -----
logger = logging.getLogger("reporte_incumplimiento")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s'))
    logger.addHandler(handler)

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

# Menú desplegable opciones
REPORTE_MOTIVOS = [
    discord.SelectOption(label="No apoyó en 𝕏", description="No cumplió con el apoyo requerido", value="no_apoyo"),
    discord.SelectOption(label="Otro (explica abajo)", description="Otra causa, requiere explicación", value="otro"),
]

# ----- ETAPAS Y MENSAJES (puedes mover a /mensajes/ luego) -----
ADVERTENCIA_1 = (
    "🚨 **Advertencia oficial**\n"
    "Hemos recibido un reporte indicando que **no apoyaste correctamente** a un compañero en X.\n\n"
    "Por favor, regulariza tu situación antes de avanzar a sanciones."
)
RECORDATORIO_2 = (
    "⏰ **Segundo recordatorio:**\n"
    "Sigue pendiente un reporte de que no has cumplido el apoyo requerido en X.\n"
    "Tienes una última oportunidad antes de sanción temporal."
)
BANEO_24H = (
    "⛔ **Has sido baneado temporalmente (24h)** por no cumplir el apoyo requerido en X tras varios avisos.\n"
    "Puedes regularizar tu situación al volver para evitar sanciones más graves."
)
BANEO_7D = (
    "⛔ **Has sido baneado 7 días** por no cumplir reiteradamente el apoyo en X. Si no se regulariza, se procederá a expulsión permanente."
)
EXPULSION_FINAL = (
    "🚫 **Has sido expulsado del servidor** por incumplir reiteradamente las normas de apoyo. Puedes apelar contactando a un administrador."
)
AGRADECIMIENTO_REPORTANTE = (
    "✅ Tu reporte ha sido procesado y el caso cerrado.\n¡Gracias por ayudar a mantener la calidad y apoyo en la comunidad!"
)
AGRADECIMIENTO_REPORTADO = (
    "🤝 El reporte sobre tu apoyo en X ha sido cerrado. Recuerda siempre cumplir para evitar sanciones. ¡Estamos para crecer juntos!"
)

INSTRUCCIONES_DM_REPORTANTE = (
    "🔎 **Tu reporte ha sido abierto.**\nTe avisaremos de cada avance.\nCuando el usuario regularice, debes confirmar aquí."
)

# ---- Función util para fechas -----
def ahora_dt():
    return datetime.now(timezone.utc)

def fecha_str():
    dt = ahora_dt().astimezone()  # Tu zona horaria real la puedes ajustar si quieres
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# -------------- COG PRINCIPAL --------------

class ReporteIncumplimiento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.init_mensaje_instrucciones())

    async def init_mensaje_instrucciones(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_REPORTE)
        if not canal:
            logger.error("No se encontró el canal de reportes.")
            return

        hash_key = "reporte_incumplimiento:instrucciones_hash"
        msg_id_key = "reporte_incumplimiento:instrucciones_msg_id"

        embed = discord.Embed(
            title=TITULO_INSTRUCCIONES,
            description=DESCRIPCION_INSTRUCCIONES,
            color=discord.Color.red(),
            timestamp=ahora_dt()
        )
        embed.set_footer(text=FOOTER)

        hash_actual = f"{TITULO_INSTRUCCIONES}|{DESCRIPCION_INSTRUCCIONES}|{FOOTER}"
        hash_guardado = self.redis.get(hash_key)
        msg_id_guardado = self.redis.get(msg_id_key)

        if msg_id_guardado and hash_guardado == hash_actual:
            try:
                mensaje = await canal.fetch_message(int(msg_id_guardado))
                # Si todo coincide no hacemos nada
                if mensaje and mensaje.embeds and mensaje.embeds[0].description == DESCRIPCION_INSTRUCCIONES:
                    logger.info("Mensaje de instrucciones ya está actualizado.")
                    return
            except Exception as e:
                logger.warning(f"No se pudo recuperar mensaje anterior de instrucciones: {e}")

        # Editar si ya existe, sino crear y fijar
        msg = None
        if msg_id_guardado:
            try:
                mensaje = await canal.fetch_message(int(msg_id_guardado))
                if mensaje:
                    await mensaje.edit(embed=embed, view=ReporteMenuView(self))
                    msg = mensaje
            except Exception as e:
                logger.warning(f"No se pudo editar mensaje anterior: {e}")

        if not msg:
            msg = await canal.send(embed=embed, view=ReporteMenuView(self))
            await msg.pin()

        self.redis.set(hash_key, hash_actual)
        self.redis.set(msg_id_key, str(msg.id))
        logger.info("Instrucciones del canal de reporte actualizadas y fijadas.")

    # --- Método para crear reporte (llamado desde el menú) ---
    async def crear_reporte(self, reportante: discord.Member, motivo: str, explicacion: str = None):
        canal = self.bot.get_channel(CANAL_REPORTE)
        canal_logs = self.bot.get_channel(CANAL_LOGS)
        report_id = self.redis.incr("reporte_incumplimiento:contador")
        clave_reporte = f"reporte_incumplimiento:reporte:{report_id}"

        # Paso 1: preguntar a quién reporta (solo miembros humanos)
        # Utiliza un modal de Discord para pedir el @usuario (autocomplete sería más pro, pero así es seguro)
        class ModalUsuario(ui.Modal, title="¿A quién reportas?"):
            usuario = ui.TextInput(label="Menciona al usuario o pon su ID", style=discord.TextStyle.short)
            razon = None
            if motivo == "otro":
                razon = ui.TextInput(label="Explica brevemente el motivo", style=discord.TextStyle.paragraph, required=True, max_length=120)

            async def on_submit(self, interaction: discord.Interaction):
                target = None
                content = self.usuario.value.strip()
                if content.startswith("<@") and content.endswith(">"):
                    try:
                        user_id = int(content.replace("<@", "").replace("!", "").replace(">", ""))
                        target = interaction.guild.get_member(user_id)
                    except:
                        pass
                else:
                    try:
                        user_id = int(content)
                        target = interaction.guild.get_member(user_id)
                    except:
                        pass

                if not target or target.bot:
                    await interaction.response.send_message("❌ Usuario inválido o es un bot.", ephemeral=True, delete_after=10)
                    return

                razon_text = self.razon.value.strip() if self.razon else explicacion

                # Guardar el reporte en Redis
                self_cog = self.children[0].cog_ref
                data_reporte = {
                    "id": report_id,
                    "fecha": fecha_str(),
                    "motivo": motivo,
                    "explicacion": razon_text or "",
                    "reportante_id": str(reportante.id),
                    "reportado_id": str(target.id),
                    "estado": "abierto",
                    "etapa": "advertencia",
                    "historial": f"Apertura: {fecha_str()}",
                }
                self_cog.redis.hset(clave_reporte, mapping=data_reporte)

                # Notificar en canal (mensaje temporal)
                embed = discord.Embed(
                    title=f"🔎 Reporte #{report_id} abierto",
                    description=f"{reportante.mention} ha reportado a {target.mention}\nMotivo: {motivo}\nFecha: {fecha_str()}",
                    color=discord.Color.yellow()
                )
                embed.set_footer(text="Este aviso se eliminará en 60s")
                msg = await canal.send(embed=embed, delete_after=60)
                logger.info(f"Reporte #{report_id} abierto por {reportante.display_name} contra {target.display_name}")
                if canal_logs:
                    await canal_logs.send(embed=embed)

                # DM al reportante (con botón de confirmar o cancelar)
                embed_dm = discord.Embed(
                    title=f"🔎 Reporte #{report_id} abierto",
                    description=f"Has reportado a {target.mention} por: {motivo}\n\n{INSTRUCCIONES_DM_REPORTANTE}",
                    color=discord.Color.yellow()
                )
                await reportante.send(embed=embed_dm, view=ReporteControlView(self_cog, report_id, reportante.id, target.id))

                # DM al reportado (advertencia y botón de confirmar que cumplió)
                embed_advert = discord.Embed(
                    title="🚨 Has recibido un reporte de apoyo",
                    description=f"Motivo: {motivo}\n\n{ADVERTENCIA_1}",
                    color=discord.Color.red()
                )
                await target.send(embed=embed_advert, view=ReportadoControlView(self_cog, report_id, reportante.id, target.id))

        # Lanza el modal
        modal = ModalUsuario()
        # Hack para acceder a la cog en el modal
        modal.children[0].cog_ref = self
        await reportante.send("📝 Completa el reporte indicando a quién deseas reportar:")
        await reportante.send_modal(modal)

# --- VIEW DEL MENÚ PRINCIPAL (instrucciones) ---
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

# --- VIEW PARA EL REPORTANTE: Confirmar/Cerrar el reporte ---
class ReporteControlView(ui.View):
    def __init__(self, cog, report_id, reportante_id, reportado_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.report_id = report_id
        self.reportante_id = reportante_id
        self.reportado_id = reportado_id

    @ui.button(label="✅ Confirmar cumplimiento", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.reportante_id):
            await interaction.response.send_message("❌ Solo el reportante puede confirmar.", ephemeral=True)
            return

        clave = f"reporte_incumplimiento:reporte:{self.report_id}"
        self.cog.redis.hset(clave, "estado", "cerrado")
        self.cog.redis.hset(clave, "etapa", "resuelto")
        self.cog.redis.hset(clave, "historial", f"{self.cog.redis.hget(clave, 'historial')}\nCerrado: {fecha_str()}")

        # Notificar a ambos por DM
        reportante = await self.cog.bot.fetch_user(int(self.reportante_id))
        reportado = await self.cog.bot.fetch_user(int(self.reportado_id))
        await reportante.send(AGRADECIMIENTO_REPORTANTE)
        await reportado.send(AGRADECIMIENTO_REPORTADO)

        # Logs
        canal_logs = self.cog.bot.get_channel(CANAL_LOGS)
        embed = discord.Embed(
            title=f"✅ Reporte #{self.report_id} cerrado",
            description=f"El reporte fue resuelto satisfactoriamente y cerrado por {reportante.mention}.",
            color=discord.Color.green(),
            timestamp=ahora_dt()
        )
        if canal_logs:
            await canal_logs.send(embed=embed)
        await interaction.response.send_message("Reporte cerrado y ambas partes notificadas.", ephemeral=True)
        self.stop()

    @ui.button(label="❌ Cancelar reporte", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.reportante_id):
            await interaction.response.send_message("❌ Solo el reportante puede cancelar.", ephemeral=True)
            return

        clave = f"reporte_incumplimiento:reporte:{self.report_id}"
        self.cog.redis.hset(clave, "estado", "cancelado")
        self.cog.redis.hset(clave, "etapa", "cancelado")
        self.cog.redis.hset(clave, "historial", f"{self.cog.redis.hget(clave, 'historial')}\nCancelado: {fecha_str()}")
        # Notificar por DM y logs
        reportante = await self.cog.bot.fetch_user(int(self.reportante_id))
        await reportante.send("Reporte cancelado por ti. No se tomaron acciones.")
        canal_logs = self.cog.bot.get_channel(CANAL_LOGS)
        embed = discord.Embed(
            title=f"❌ Reporte #{self.report_id} cancelado",
            description=f"El reporte fue cancelado por el reportante {reportante.mention}.",
            color=discord.Color.greyple(),
            timestamp=ahora_dt()
        )
        if canal_logs:
            await canal_logs.send(embed=embed)
        await interaction.response.send_message("Reporte cancelado y registrado en logs.", ephemeral=True)
        self.stop()

# --- VIEW PARA EL REPORTADO: Confirmar que cumplió (luego, el reportante debe validar) ---
class ReportadoControlView(ui.View):
    def __init__(self, cog, report_id, reportante_id, reportado_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.report_id = report_id
        self.reportante_id = reportante_id
        self.reportado_id = reportado_id
        self.intentos = int(self.cog.redis.hget(f"reporte_incumplimiento:reporte:{self.report_id}", "intentos") or 0)

    @ui.button(label="✅ Ya cumplí (apoyé en X)", style=discord.ButtonStyle.primary)
    async def cumplio(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.reportado_id):
            await interaction.response.send_message("❌ Solo el usuario reportado puede usar este botón.", ephemeral=True)
            return

        clave = f"reporte_incumplimiento:reporte:{self.report_id}"
        self.intentos += 1
        self.cog.redis.hset(clave, "etapa", f"verificacion_{self.intentos}")
        self.cog.redis.hset(clave, "historial", f"{self.cog.redis.hget(clave, 'historial')}\nIntento de cumplimiento: {fecha_str()}")
        self.cog.redis.hset(clave, "intentos", str(self.intentos))

        # Notificar al reportante para validar
        reportante = await self.cog.bot.fetch_user(int(self.reportante_id))
        await reportante.send(
            f"⚠️ El usuario {interaction.user.mention} dice que ya cumplió con el apoyo en X.\n\n"
            "¿Es correcto? Si es así, usa el botón de confirmar cumplimiento en tu DM para cerrar el reporte. "
            "Si no es así, puedes rechazar el intento."
        )
        await interaction.response.send_message("Notificamos al reportante para que valide. Si acepta, se cerrará el reporte.", ephemeral=True)

    @ui.button(label="❌ Rechazar (no cumplió)", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.reportante_id):
            await interaction.response.send_message("❌ Solo el reportante puede rechazar un intento de cumplimiento.", ephemeral=True)
            return

        clave = f"reporte_incumplimiento:reporte:{self.report_id}"
        self.intentos = int(self.cog.redis.hget(clave, "intentos") or 1)
        self.cog.redis.hset(clave, "etapa", f"rechazo_{self.intentos}")
        self.cog.redis.hset(clave, "historial", f"{self.cog.redis.hget(clave, 'historial')}\nRechazo intento: {fecha_str()}")
        # Lógica de advertencias/baneos/expulsión
        # Si rechaza 3 veces: aplicar sanción progresiva
        if self.intentos == 1:
            msg = RECORDATORIO_2
        elif self.intentos == 2:
            msg = BANEO_24H
            # Aquí puedes llamar lógica de ban temporal
        elif self.intentos == 3:
            msg = BANEO_7D
            # Aquí puedes llamar lógica de ban 7d
        elif self.intentos >= 4:
            msg = EXPULSION_FINAL
            self.cog.redis.hset(clave, "estado", "expulsado")
            # Aquí puedes llamar lógica de expulsión real

        # Notificar al reportado (y logs)
        reportado = await self.cog.bot.fetch_user(int(self.reportado_id))
        await reportado.send(msg)
        canal_logs = self.cog.bot.get_channel(CANAL_LOGS)
        embed = discord.Embed(
            title=f"🚨 Reporte #{self.report_id} - Acción tomada",
            description=f"{msg}\n(Reporte #{self.report_id} - Intentos: {self.intentos})",
            color=discord.Color.red(),
            timestamp=ahora_dt()
        )
        if canal_logs:
            await canal_logs.send(embed=embed)
        await interaction.response.send_message("Has registrado el rechazo y se notificó al reportado. El caso sigue abierto.", ephemeral=True)

# --- SETUP ---
async def setup(bot):
    await bot.add_cog(ReporteIncumplimiento(bot))
