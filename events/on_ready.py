import discord
from discord.ext import commands
import datetime
from utils import registrar_log  # Asumo que tienes esta función para logs

async def on_ready(bot: commands.Bot):
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"Hora UTC: {datetime.datetime.utcnow().isoformat()}")
    await registrar_log("🤖 Bot listo y conectado", categoria="sistema")

def setup(bot: commands.Bot):
    bot.event(bot.loop.create_task(on_ready(bot)))
