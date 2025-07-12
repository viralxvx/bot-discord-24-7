import discord
from discord.ext import commands
from discord import app_commands
from config import ADMIN_ID, REDIS_URL, CANAL_COMANDOS_ID
import redis
from datetime import datetime, timezone
import json

class Auditoria(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(
        name="auditoria",
        description="Ver auditoría completa de faltas, inactividad y prórrogas de un usuario (solo admins)."
    )
    @app_commands.describe(usuario="Usuario a auditar")
    async def auditoria(self, interaction: discord.Interaction, usuario: discord.Member):
        if interaction.user.id != int(ADMIN_ID):
            await interaction.response.send_message(
                "❌ Solo los administradores pueden usar este comando.",
                ephemeral=True
            )
            return
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal de comandos.",
                ephemeral=True
            )
            return

        user_id = usuario.id
        data = self.redis.hgetall(f"usuario:{user_id}")
        estado = data.get("estado", "Activo").capitalize()
        faltas_total = int(data.get("faltas_totales", 0))
        faltas_mes = int(data.get("faltas_mes", 0))
        ultima_falta = data.get("ultima_falta")
        try:
            ultima_falta_dt = datetime.fromtimestamp(float(ultima_falta), timezone.utc) if ultima_falta else None
        except:
            ultima_falta_dt = None

        # Fecha de ingreso
        fecha_ingreso = usuario.joined_at.strftime('%Y-%m-%d') if usuario.joined_at else "-"

        # HISTORIAL COMPLETO DE FALTAS
        faltas_hist = self.redis.lrange(f"faltas_historial:{user_id}", 0, -1)
        faltas_historial = []
        if faltas_hist:
            for falta in faltas_hist[-10:]:
                try:
                    entry = json.loads(falta)
                    faltas_historial.append(f"`{entry['fecha']}`: {entry['motivo']} ({entry['canal']}) — {entry['moderador']}")
                except:
                    faltas_historial.append(falta)
        faltas_historial_text = "\n".join(faltas_historial) if faltas_historial else "*Sin faltas registradas*"

        # HISTORIAL COMPLETO DE PRÓRROGAS
        prorroga_hist = self.redis.lrange(f"prorrogas_historial:{user_id}", 0, -1)
        prorroga_historial = []
        if prorroga_hist:
            for pr in prorroga_hist[-5:]:
                try:
                    entry = json.loads(pr)
                    prorroga_historial.append(
                        f"`{entry['fecha']}`: {entry['duracion']} — Motivo: {entry['motivo']} (por {entry['otorgada_por']})"
                    )
                except:
                    prorroga_historial.append(pr)
        prorroga_historial_text = "\n".join(prorroga_historial) if prorroga_historial else "*Sin prórrogas históricas*"

        # HISTORIAL DE INACTIVIDAD Y SANCIONES
        inactividad_hist = self.redis.lrange(f"inactividad_historial:{user_id}", 0, -1)
        inact_historial = []
        if inactividad_hist:
            for h in inactividad_hist[-8:]:
                try:
                    entry = json.loads(h)
                    inact_historial.append(f"`{entry['fecha']}`: {entry['accion']} — {entry['detalle']}")
                except:
                    inact_historial.append(h)
        inact_historial_text = "\n".join(inact_historial) if inact_historial else "*Sin historial de inactividad*"

        reincidencias = int(self.redis.get(f"inactividad:reincidencia:{user_id}") or 0)
        advertencias = int(self.redis.get(f"inactividad:advertencias:{user_id}") or 0)
        prorroga_activa = self.redis.get(f"inactividad:prorroga:{user_id}")
        prorroga_text = "-"
        if prorroga_activa:
            prorroga_dt = datetime.fromisoformat(prorroga_activa)
            prorroga_text = f"Hasta <t:{int(prorroga_dt.timestamp())}:R>"

        last_publi = self.redis.get(f"inactividad:{user_id}")
        last_publi_dt = datetime.fromisoformat(last_publi) if last_publi else None

        avatar_url = getattr(getattr(usuario, "display_avatar", None), "url", "") or getattr(getattr(usuario, "avatar", None), "url", "")
        embed = discord.Embed(
            title=f"🕵️‍♂️ Auditoría de {usuario.display_name} ({usuario.id})",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Estado actual", value=estado, inline=True)
        embed.add_field(name="Faltas totales", value=faltas_total, inline=True)
        embed.add_field(name="Faltas este mes", value=faltas_mes, inline=True)
        embed.add_field(name="Fecha de ingreso", value=fecha_ingreso, inline=True)
        if ultima_falta_dt:
            embed.add_field(name="Última falta", value=f"<t:{int(ultima_falta_dt.timestamp())}:R>", inline=True)
        if last_publi_dt:
            embed.add_field(name="Última publicación", value=f"<t:{int(last_publi_dt.timestamp())}:R>", inline=True)
        embed.add_field(name="Prórroga activa", value=prorroga_text, inline=True)
        embed.add_field(name="Advertencias activas", value=advertencias, inline=True)
        embed.add_field(name="Reincidencias inactividad", value=reincidencias, inline=True)
        embed.add_field(name="Historial de faltas", value=faltas_historial_text, inline=False)
        embed.add_field(name="Historial de prórrogas", value=prorroga_historial_text, inline=False)
        embed.add_field(name="Historial de inactividad/sanciones", value=inact_historial_text, inline=False)
        embed.set_footer(text="VXBot Auditoría | Última revisión")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Auditoria(bot))
