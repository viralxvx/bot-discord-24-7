import discord
from handlers import logs

CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_X_NORMAS = "𝕏-normas"

async def on_member_join(member):
    # Código para manejar entrada de miembros, si tienes
    pass

async def on_member_remove(member):
    # Código para manejar salida de miembros, si tienes
    pass

async def on_message(message, bot):
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        from handlers import reporte_incumplimiento
        await reporte_incumplimiento.manejar_reporte_incumplimiento(message, bot)

    elif message.channel.name == CANAL_X_NORMAS and not message.author.bot:
        from handlers import x_normas
        await x_normas.algun_manejador(message, bot)  # Cambia 'algun_manejador' por la función real que uses

    await logs.registrar_log(f"Mensaje recibido en {message.channel.name} por {message.author}", categoria="eventos")
