from discord.ext import tasks
import discord

@tasks.loop(minutes=30)
async def verificar_inactividad():
    from discord_bot import bot  # Evita import circular
    await bot.wait_until_ready()
    
    # Aquí puedes poner tu lógica de verificación
    print("✅ Verificación de inactividad ejecutada.")
