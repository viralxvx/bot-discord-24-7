import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timezone

from utils.logger import log_discord

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONES = [
    "canales.presentate",
    "canales.normas_generales",
    "canales.faltas",
    "canales.comandos",
    "canales.inactividad",
    "canales.soporte_prorroga",
    "canales.go_viral",
    "comandos.prorroga",
    "comandos.override",
    "canales.reporte_incumplimiento",
    "comandos",
]

@bot.event
async def on_ready():
    await log_discord(
        bot,
        message=f"Bot conectado como **{bot.user}**\nHora: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        level="success",
        title="✅ Bot iniciado correctamente"
    )

    for ext in EXTENSIONES:
        try:
            await bot.load_extension(ext)
            await log_discord(
                bot,
                message=f"Módulo **{ext}** cargado correctamente.",
                level="success",
                title="Módulo cargado"
            )
        except Exception as e:
            await log_discord(
                bot,
                message=f"Error al cargar **{ext}**:\n{e}",
                level="error",
                title="❌ Error al cargar módulo"
            )

    try:
        synced = await bot.tree.sync()
        await log_discord(
            bot,
            message=f"{len(synced)} comandos sincronizados.",
            level="info",
            title="🔁 Comandos slash sincronizados"
        )
    except Exception as e:
        await log_discord(
            bot,
            message=f"Error al sincronizar comandos: {e}",
            level="error",
            title="❌ Error al sincronizar comandos"
        )

    # Previene apagado por inactividad
    while True:
        await asyncio.sleep(60)
        print("⏳ Bot sigue vivo...")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.lower() == "hola bot":
        await message.channel.send("👋 ¡Hola, soy VXbot y estoy vivo!")
    await bot.process_commands(message)

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    asyncio.run(bot.start(TOKEN))
