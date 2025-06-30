# tasks/verificar_inactividad.py
from discord.ext import tasks

@tasks.loop(minutes=30)
async def verificar_inactividad():
    from bot_instance import bot  # Importar dentro para evitar import circular
    await bot.wait_until_ready()
    # Aquí pones la lógica para verificar inactividad
