import discord
from views.report_menu import ReportMenu  # Importación corregida
from config import CANAL_REPORTES
from state_management import mensajes_recientes, save_state

async def handle_reporte_message(message):
    if message.author.bot:
        return
        
    if message.mentions:
        reportado = message.mentions[0]
        await message.channel.send(
            f"📃 **Reportando a {reportado.mention}**",
            view=ReportMenu(reportado, message.author)
        )
        await message.delete()
    else:
        await message.channel.send("⚠️ **Menciona un usuario** o usa `!permiso <días>`")
