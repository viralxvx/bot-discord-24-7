# comandos/__init__.py

import os
from discord.ext import commands

async def setup(bot: commands.Bot):
    from .estado import setup as setup_estado
    from .estadisticas import setup as setup_estadisticas

    await setup_estado(bot)
    await setup_estadisticas(bot)

    print("✅ Comandos /estado y /estadisticas registrados.")
