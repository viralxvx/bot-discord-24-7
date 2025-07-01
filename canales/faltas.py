from config import CANAL_FALTAS
from state_management import RedisState

async def registrar_falta(user, motivo, channel):
    redis_state = RedisState()
    redis_state.increment_falta(user.id, motivo)
    await channel.guild.get_channel(CANAL_FALTAS).send(f"Falta registrada para {user.mention}: {motivo}")

async def enviar_advertencia(user, motivo, channel):
    await user.send(f"⚠️ Falta: {motivo}")
    await channel.guild.get_channel(CANAL_FALTAS).send(f"Advertencia enviada a {user.mention}: {motivo}")

async def actualizar_estado_usuario(user):
    redis_state = RedisState()
    faltas = redis_state.get_faltas(user.id)
    # Aquí puedes agregar lógica para sanciones (ej. expulsión tras X faltas)
    return faltas
