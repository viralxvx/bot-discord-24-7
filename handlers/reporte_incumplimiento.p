import discord
from .logs import registrar_log

CANAL_REPORTES = "⛔reporte-de-incumplimiento"

async def manejar_reporte_incumplimiento(message, bot):
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        if message.mentions:
            reportado = message.mentions[0]
            await message.channel.send(
                f"📃 **Reportando a {reportado.mention}**"
            )
            await registrar_log(f"Reporte hecho por {message.author.name} contra {reportado.name}", categoria="reportes")
        else:
            await message.channel.send("⚠️ **Menciona un usuario para reportar**")
