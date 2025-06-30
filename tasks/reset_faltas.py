from discord.ext import tasks
import discord

@tasks.loop(hours=24)
async def reset_faltas():
    from discord_bot import bot  # Importar aquí para evitar importación circular

    await bot.wait_until_ready()
    # Código para resetear faltas
