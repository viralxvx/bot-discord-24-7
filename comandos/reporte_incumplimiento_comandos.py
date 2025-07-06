"""
=======================================================================================
 Archivo: comandos/reporte_incumplimiento_comandos.py
 Autor:    Viral X | VXbot (Miguel Peralta & ChatGPT)
 Creado:   2025-07
---------------------------------------------------------------------------------------
 PROPÓSITO:
 Comandos slash para consulta, auditoría y gestión del sistema automatizado de reportes.
 
 Incluye comandos de usuario (/mis-reportes) y de staff (/panel-reporte, /forzar-cierre).
 Usa únicamente los textos centralizados en mensajes/reporte_incumplimiento_mensajes.py

---------------------------------------------------------------------------------------
 PARA DESARROLLADORES:
 - Todos los comandos deben ser robustos y blindados contra abuso.
 - Los comandos de staff (panel y forzar cierre) solo pueden usarse por staff/admin.
 - El historial mostrado es en tiempo real y muestra la trazabilidad de cada caso.
 - No modificar la lógica del ciclo de advertencias aquí. Solo gestión/consulta.
=======================================================================================
"""

import discord
from discord.ext import commands
import redis

from mensajes import reporte_incumplimiento_mensajes as MSG
from config import REDIS_URL, CANAL_LOGS_ID
from utils.logger import log_discord

def es_staff_or_admin(member):
    return member.guild_permissions.manage_guild or member.guild_permissions.administrator

class ComandosReporteIncumplimiento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    # --- Comando /mis-reportes ---
    @commands.slash_command(name="mis-reportes", description="Consulta tus reportes abiertos y cerrados")
    async def mis_reportes(self, ctx):
        user_id = str(ctx.author.id)
        keys = self.redis.keys("reporte_inc:*")
        encontrados = []

        for key in keys:
            data = self.redis.hgetall(key)
            # Reportante o reportado
            reportantes = set(data.get("reportantes", "").split(",")) if data.get("reportantes") else set()
            if user_id == data.get("reportado_id") or user_id in reportantes:
                encontrados.append(data)

        if not encontrados:
            await ctx.respond("No tienes reportes activos ni historial.", ephemeral=True)
            return

        embeds = []
        for data in encontrados:
            estado = data.get("estado", "desconocido")
            fecha = data.get("historial", "").split("\n")[0] if data.get("historial") else "Sin fecha"
            embed = discord.Embed(
                title=f"Reporte {'en tu contra' if user_id == data.get('reportado_id') else 'realizado por ti'}",
                description=f"**Estado:** {estado}\n"
                            f"**Advertencias:** {data.get('advertencias', '1')}\n"
                            f"**Historial:**\n{data.get('historial','')}\n"
                            f"**Reportantes:** {data.get('reportantes','')}\n",
                color=discord.Color.orange() if estado == "abierto" else discord.Color.green() if estado == "cerrado" else discord.Color.red()
            )
            embeds.append(embed)

        for embed in embeds:
            await ctx.author.send(embed=embed)
        await ctx.respond("Te he enviado tu historial de reportes por DM.", ephemeral=True)

    # --- Comando /panel-reporte (solo staff/admin) ---
    @commands.slash_command(name="panel-reporte", description="Panel de gestión y auditoría de todos los reportes")
    async def panel_reporte(self, ctx):
        if not es_staff_or_admin(ctx.author):
            await ctx.respond("Solo el staff/admin puede usar este comando.", ephemeral=True)
            return

        keys = self.redis.keys("reporte_inc:*")
        if not keys:
            await ctx.respond("No hay reportes en curso.", ephemeral=True)
            return

        embeds = []
        for key in keys:
            data = self.redis.hgetall(key)
            estado = data.get("estado", "desconocido")
            fecha = data.get("historial", "").split("\n")[0] if data.get("historial") else "Sin fecha"
            embed = discord.Embed(
                title=f"Reporte de {data.get('reportado_id','')} (Estado: {estado})",
                description=f"**Reportantes:** {data.get('reportantes','')}\n"
                            f"**Advertencias:** {data.get('advertencias','1')}\n"
                            f"**Historial:**\n{data.get('historial','')}",
                color=discord.Color.orange() if estado == "abierto" else discord.Color.green() if estado == "cerrado" else discord.Color.red()
            )
            embeds.append(embed)
        await ctx.respond("Panel de reportes abiertos:", embeds=embeds, ephemeral=True)

    # --- Comando /forzar-cierre (solo staff/admin) ---
    @commands.slash_command(name="forzar-cierre", description="Forzar el cierre manual de un reporte")
    async def forzar_cierre(self, ctx, reportado_id: discord.Option(str, "ID del usuario reportado")):
        if not es_staff_or_admin(ctx.author):
            await ctx.respond("Solo el staff/admin puede usar este comando.", ephemeral=True)
            return

        key = f"reporte_inc:{reportado_id}"
        data = self.redis.hgetall(key)
        if not data or data.get("estado") == "cerrado":
            await ctx.respond(f"No se encontró un reporte activo para el usuario {reportado_id}.", ephemeral=True)
            return

        self.redis.hset(key, mapping={
            "estado": "cerrado",
            "historial": data.get("historial", "") + f"Forzado por staff {ctx.author.display_name}\n"
        })
        await ctx.respond(f"Reporte contra {reportado_id} cerrado forzadamente.", ephemeral=True)
        await log_discord(self.bot, MSG.AVISO_STAFF_FORZADO.format(reporte_id=reportado_id))

async def setup(bot):
    await bot.add_cog(ComandosReporteIncumplimiento(bot))
