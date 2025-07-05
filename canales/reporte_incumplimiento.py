import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import redis
from datetime import datetime, timezone
from config import CANAL_REPORTE_ID, CANAL_LOGS_ID, REDIS_URL

INSTRUCCIONES_REPORTE = (
    "🚨 **REPORTE DE INCUMPLIMIENTO EN X**\n\n"
    "¿Algún usuario no te ha apoyado correctamente en X tras tu publicación en #🧵go-viral?\n\n"
    "Selecciona el motivo del reporte en el menú abajo y sigue los pasos. El proceso será **totalmente confidencial** y guiado por el bot.\n\n"
    "⛔ *Abusar de los reportes puede resultar en sanción.*\n\n"
    "👉 Solo reacciona si realmente has verificado el incumplimiento.\n"
    "🕒 Los reportes serán gestionados automáticamente, recibirás instrucciones por DM.\n\n"
    "Última actualización: {fecha}"
)

OPCIONES_MOTIVO = [
    discord.SelectOption(label="No apoyó en 𝕏", description="No recibiste apoyo después de tu publicación."),
    discord.SelectOption(label="Otro (requiere explicación corta)", description="Indica brevemente el motivo.", emoji="✍️")
]

class MenuMotivoReporte(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.select(
        placeholder="Selecciona el motivo del reporte",
        min_values=1, max_values=1,
        options=OPCIONES_MOTIVO
    )
    async def motivo_callback(self, interaction: discord.Interaction, select: ui.Select):
        motivo = select.values[0]
        user = interaction.user

        # Solo permite un reporte abierto por usuario
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        key_reporte = f"reporte:abierto:{user.id}"
        if r.exists(key_reporte):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Ya tienes un reporte abierto",
                    description="Por favor, termina tu reporte anterior antes de crear uno nuevo.",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )
            return

        fecha_str = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")
        if motivo == "Otro (requiere explicación corta)":
            # Solicitar explicación corta
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✍️ Explica brevemente tu motivo",
                    description="Por favor, escribe en el chat privado (DM) una explicación corta del motivo del reporte.",
                    color=discord.Color.blue()
                ),
                ephemeral=True
            )
            # Marcar en Redis que espera explicación, el siguiente mensaje del usuario será la explicación
            r.set(f"reporte:esperando_exp:{user.id}", "1", ex=300)
            r.set(key_reporte, "1", ex=600)
        else:
            # Inicia reporte estándar (No apoyó en X)
            await self.abrir_reporte(interaction, user, motivo, fecha_str)

    async def abrir_reporte(self, interaction, user, motivo, fecha_str):
        # Registro en Redis del reporte
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        key_reporte = f"reporte:abierto:{user.id}"
        r.set(key_reporte, "1", ex=600)
        r.hset(f"reporte:detalle:{user.id}", mapping={
            "usuario": user.id,
            "motivo": motivo,
            "estado": "abierto",
            "fecha": fecha_str
        })

        # Log en canal logs
        logs = interaction.guild.get_channel(CANAL_LOGS_ID)
        if logs:
            await logs.send(
                embed=discord.Embed(
                    title="📝 Nuevo reporte de incumplimiento",
                    description=f"**Usuario:** {user.mention}\n**Motivo:** {motivo}\n**Fecha:** {fecha_str}",
                    color=discord.Color.blurple()
                )
            )
        # Aviso temporal en canal reporte
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Reporte abierto",
                description="Tu reporte fue registrado. El bot continuará el proceso por DM. Gracias por contribuir al crecimiento justo.",
                color=discord.Color.green()
            ),
            ephemeral=True,
            delete_after=15
        )
        # DM al usuario confirmando apertura
        try:
            await user.send(
                embed=discord.Embed(
                    title="🚩 Reporte abierto",
                    description=f"Has iniciado un reporte por el motivo: **{motivo}**\nFecha/hora: {fecha_str}\n\nSigue las instrucciones del bot para completar el proceso.",
                    color=discord.Color.blue()
                )
            )
        except:
            pass

class ReporteIncumplimiento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.instrucciones_hash = None
        bot.loop.create_task(self.publicar_instrucciones_fijas())

    async def publicar_instrucciones_fijas(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_REPORTE_ID)
        if not canal:
            print("❌ [REPORTE] No se encontró el canal de reportes.")
            return

        # Calcula hash del texto de instrucciones para evitar duplicados innecesarios
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        instrucciones = INSTRUCCIONES_REPORTE.format(fecha=fecha_actual)
        hash_nuevo = hash(instrucciones)

        msg_id_guardado = self.redis.get("reporte:msg_instrucciones_id")
        hash_guardado = self.redis.get("reporte:msg_instrucciones_hash")

        if msg_id_guardado:
            try:
                mensaje = await canal.fetch_message(int(msg_id_guardado))
                if mensaje and mensaje.embeds:
                    embed_actual = mensaje.embeds[0]
                    hash_actual = hash(embed_actual.description)
                    if hash_actual == hash_nuevo:
                        print("✅ [REPORTE] Instrucciones ya están actualizadas.")
                        return
                    else:
                        embed = discord.Embed(
                            title="⛔ Reporte de Incumplimiento",
                            description=instrucciones,
                            color=discord.Color.red()
                        )
                        await mensaje.edit(embed=embed, view=MenuMotivoReporte(self.bot))
                        self.redis.set("reporte:msg_instrucciones_hash", hash_nuevo)
                        print("🔄 [REPORTE] Instrucciones de reporte actualizadas.")
                        return
            except Exception as e:
                print(f"⚠️ [REPORTE] No se pudo recuperar el mensaje de instrucciones: {e}")

        embed = discord.Embed(
            title="⛔ Reporte de Incumplimiento",
            description=instrucciones,
            color=discord.Color.red()
        )
        msg = await canal.send(embed=embed, view=MenuMotivoReporte(self.bot))
        self.redis.set("reporte:msg_instrucciones_id", str(msg.id))
        self.redis.set("reporte:msg_instrucciones_hash", hash_nuevo)
        print("✅ [REPORTE] Instrucciones publicadas y registradas.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Si está esperando explicación del reporte "Otro"
        if message.guild is not None or message.author.bot:
            return
        if self.redis.get(f"reporte:esperando_exp:{message.author.id}"):
            motivo = message.content.strip()[:100]
            fecha_str = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")
            # Borra el flag y abre reporte
            self.redis.delete(f"reporte:esperando_exp:{message.author.id}")
            view = MenuMotivoReporte(self.bot)
            # Simula la apertura del reporte con explicación personalizada
            await view.abrir_reporte_dummy(message.author, motivo, fecha_str)
            await message.author.send(
                embed=discord.Embed(
                    title="✉️ Motivo recibido",
                    description=f"Tu reporte fue registrado con el motivo: {motivo}\nFecha/hora: {fecha_str}",
                    color=discord.Color.green()
                )
            )

    # Método extra para soporte de explicación personalizada desde DM
    async def abrir_reporte_dummy(self, user, motivo, fecha_str):
        r = self.redis
        key_reporte = f"reporte:abierto:{user.id}"
        r.set(key_reporte, "1", ex=600)
        r.hset(f"reporte:detalle:{user.id}", mapping={
            "usuario": user.id,
            "motivo": motivo,
            "estado": "abierto",
            "fecha": fecha_str
        })
        guild = None
        for g in self.bot.guilds:
            if g.get_member(user.id):
                guild = g
                break
        if guild:
            logs = guild.get_channel(CANAL_LOGS_ID)
            if logs:
                await logs.send(
                    embed=discord.Embed(
                        title="📝 Nuevo reporte de incumplimiento",
                        description=f"**Usuario:** {user.mention}\n**Motivo:** {motivo}\n**Fecha:** {fecha_str}",
                        color=discord.Color.blurple()
                    )
                )

async def setup(bot):
    await bot.add_cog(ReporteIncumplimiento(bot))
