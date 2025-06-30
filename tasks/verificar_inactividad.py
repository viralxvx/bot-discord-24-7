from discord.ext import tasks

@tasks.loop(minutes=30)
async def verificar_inactividad():
    from discord_bot import bot  # Importación tardía para evitar circularidad
    await bot.wait_until_ready()

    # Aquí va la lógica para verificar inactividad
    print("🟡 Verificando inactividad...")
