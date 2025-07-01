from config import CANAL_LOGS

async def registrar_log(accion, user, canal_original, bot):
    log_channel = bot.get_channel(CANAL_LOGS)
    if log_channel:
        await log_channel.send(f"[LOG] {accion} - Usuario: {user.mention} - Canal: {canal_original.name}")
