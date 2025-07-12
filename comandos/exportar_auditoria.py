import discord
from discord.ext import commands
from discord import app_commands
from config import ADMIN_ID, REDIS_URL, CANAL_COMANDOS_ID
import redis
from datetime import datetime, timezone
import json
import io

class ExportarAuditoria(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(
        name="exportar_auditoria",
        description="Descarga el historial completo de faltas, prórrogas y sanciones de un usuario (solo admins)."
    )
    @app_commands.describe(usuario="Usuario a exportar")
    async def exportar_auditoria(self, interaction: discord.Interaction, usuario: discord.Member):
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
        lines = []
        lines.append(f"AUDITORÍA COMPLETA - {usuario.display_name} ({usuario.id})")
        lines.append(f"Fecha de exportación: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("="*60)
        
        # Faltas
        faltas_hist = self.redis.lrange(f"faltas_historial:{user_id}", 0, -1)
        lines.append("\n[ HISTORIAL DE FALTAS ]")
        if faltas_hist:
            for falta in faltas_hist:
                try:
                    entry = json.loads(falta)
                    lines.append(f"{entry['fecha']}: {entry['motivo']} (Canal: {entry['canal']}) — Moderador: {entry['moderador']}")
                except:
                    lines.append(falta)
        else:
            lines.append("Sin faltas registradas.")
        
        # Prórrogas
        prorroga_hist = self.redis.lrange(f"prorrogas_historial:{user_id}", 0, -1)
        lines.append("\n[ HISTORIAL DE PRÓRROGAS ]")
        if prorroga_hist:
            for pr in prorroga_hist:
                try:
                    entry = json.loads(pr)
                    lines.append(f"{entry['fecha']}: {entry['duracion']} — Motivo: {entry['motivo']} (Otorgada por: {entry['otorgada_por']})")
                except:
                    lines.append(pr)
        else:
            lines.append("Sin prórrogas registradas.")

        # Inactividad/Sanciones
        inactividad_hist = self.redis.lrange(f"inactividad_historial:{user_id}", 0, -1)
        lines.append("\n[ HISTORIAL DE INACTIVIDAD/SANCIONES ]")
        if inactividad_hist:
            for h in inactividad_hist:
                try:
                    entry = json.loads(h)
                    lines.append(f"{entry['fecha']}: {entry['accion']} — {entry['detalle']}")
                except:
                    lines.append(h)
        else:
            lines.append("Sin sanciones o advertencias por inactividad.")

        lines.append("="*60)
        # Convertir a archivo
        contenido = "\n".join(lines)
        archivo = io.StringIO(contenido)
        archivo.seek(0)

        file_discord = discord.File(fp=archivo, filename=f"auditoria_{usuario.id}.txt")
        await interaction.response.send_message(
            content=f"📝 Exportación de historial completa de {usuario.display_name} ({usuario.id})",
            file=file_discord,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ExportarAuditoria(bot))
