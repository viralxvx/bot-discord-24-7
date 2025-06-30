import discord
from .logs import registrar_log

CANAL_X_NORMAS = "𝕏-normas"

async def algun_manejador(message, bot):
    # Implementa aquí la lógica que necesites para el canal x_normas
    await registrar_log(f"Mensaje en canal {CANAL_X_NORMAS} por {message.author.name}", categoria="x_normas")
