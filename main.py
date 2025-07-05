import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timezone

from utils.logger import custom_log

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

log_message = None  # Variable para almacenar el mensaje de log

@bot.event
async def on_ready():
    global log_message

    logs = []

    # Agregar la información básica del bot
    logs.append(f"Bot conectado como **{bot.user}**\nHora: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Actualizar el status mientras se carga el bot
    logs_message = "\n".join(logs)  # Unir todos los logs en un solo mensaje

    if log_message is None:
        # Si no existe el mensaje, crear uno nuevo
        log_message = await custom_log(bot, "Cargando el bot", logs_message, "🔄 Resumen de inicio del bot")
    else:
        # Si el mensaje ya existe, actualizarlo
        await log_message.edit(content=logs_message)

    # Cargar extensiones y agregar logs correspondientes
    for ext in EXTENSIONES:
        try:
            await bot.load_extension(ext)
            logs.append(f"Módulo **{ext}** cargado correctamente.")
        except Exception as e:
            logs.append(f"Error al cargar **{ext}**:\n{e}")

    # Sincronizar comandos y agregar logs correspondientes
    try:
        synced = await bot.tree.sync()
        logs.append(f"{len(synced)} comandos sincronizados.")
    except Exception as e:
        logs.append(f"Error al sincronizar comandos: {e}")

    # Unir todos los logs en un solo mensaje
    logs_message = "\n".join(logs)

    # Actualizar el mensaje de logs en Discord
    if log_message is None:
        await custom_log(bot, "Cargando el bot", logs_message, "🔄 Resumen de inicio del bot")
    else:
        await log_message.edit(content=logs_message)

    # Si todo está bien, actualizar el Status a "Activo"
    await custom_log(bot, "Activo", "Todos los módulos cargados correctamente.", "✅ Resumen de inicio del bot")

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
