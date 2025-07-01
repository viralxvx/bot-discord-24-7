from config import CANAL_LOGS

async def registrar_log(accion, user, channel):
    log_channel = channel.guild.get_channel(CANAL_LOGS)
    await log_channel.send(f"[LOG] {accion} - Usuario: {user.mention} - Canal: {channel.name}")
