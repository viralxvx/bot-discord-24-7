from discord.ext import tasks
import discord

@tasks.loop(minutes=30)
async def verificar_inactividad():
    from discord_bot import bot  # Importar aquí para evitar importación circular

    await bot.wait_until_ready()
    # Código para verificar inactividad
