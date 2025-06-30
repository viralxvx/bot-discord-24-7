import discord
import datetime

CANAL_LOGS = "📝logs"

async def registrar_log(mensaje, categoria="general"):
    # Busca el canal de logs en el primer guild del bot
    for guild in discord.utils.get_all():
        canal_logs = discord.utils.get(guild.text_channels, name=CANAL_LOGS)
        if canal_logs:
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            await canal_logs.send(f"[{timestamp}] [{categoria.upper()}] {mensaje}")
            break
