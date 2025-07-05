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

# Mensaje de log global (lo vamos a actualizar)
log_message = None

@bot.event
async def on_ready():
    global log_message

    logs = []

    # Primer log (bot conectado)
    logs.append(f"Bot conectado como **{bot.user}**\nHora: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Crear el mensaje inicial
    if not log_message:
        log_channel = bot.get_channel(int(os.getenv("CANAL_LOGS")))  # Usamos la variable de entorno para obtener el canal
        if log_channel:
            log_message = await log_channel.send("🔄 **Resumen de inicio del bot**: Cargando...")

    # Actualizar el mensaje de log
    for ext in EXTENSIONES:
        try:
            await bot.load_extension(ext)
            logs.append(f"Módulo **{ext}** cargado correctamente.")
        except Exception as e:
            logs.append(f"Error al cargar **{ext}**:\n{e}")

    try:
        synced = await bot.tree.sync()
        logs.append(f"{len(synced)} comandos sincronizados.")
    except Exception as e:
        logs.append(f"Error al sincronizar comandos: {e}")
    
    # Unir los logs y actualizar el mensaje en Discord
    logs_message = "\n".join(logs)
    
    if log_message:
        await log_message.edit(content=f"🔄 **Resumen de inicio del bot**:\n{logs_message}")

    # Prevenir apagado por inactividad
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
