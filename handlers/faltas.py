import discord
from .logs import registrar_log

CANAL_FALTAS = "📤faltas"
faltas_dict = {}

async def actualizar_mensaje_faltas(canal, usuario, faltas, aciertos, estado):
    contenido = f"{usuario.mention}: Faltas={faltas}, Aciertos={aciertos}, Estado={estado}"
    msg = await canal.send(contenido)
    await registrar_log(f"Actualizado faltas para {usuario.name}: {contenido}", categoria="faltas")
