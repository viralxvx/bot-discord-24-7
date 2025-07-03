import discord
from discord.ext import commands
import os

class Comandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Comandos(bot))

    # 🔽 Carga manual de los comandos slash
    from comandos.estado import Estado
    from comandos.estadisticas import Estadisticas

    await bot.add_cog(Estado(bot))
    await bot.add_cog(Estadisticas(bot))

    print("✅ Comandos /estado y /estadisticas registrados.")
