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
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONES = [
    "canales.presentate",
    "canales.normas_generales",
    "canales.faltas",
    "canales.comandos",
    "comandos",
    "canales.inactividad",
    "canales.soporte_prorroga",
    "canales.go_viral",
    "comandos.prorroga",
    "comandos.override",
    "canales.reporte_incumplimiento",
    "cogs.misc",
    "canales.anuncios",
    "canales.nuevas_funciones",
    "comandos.novedades",
    "canales.soporte"  
]

log_message = None  # Mensaje embed en canal de logs
logs = []  # Lista para mensaje embed y consola Railway

def get_current_time():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

@bot.event
async def on_ready():
    global log_message, logs

    logs.append(f"✅ Bot conectado como **{bot.user}**")
    logs.append(f"Hora: {get_current_time()}")

    print(f"✅ Bot conectado como {bot.user}")
    print(f"Hora: {get_current_time()}")

    errores = []
    success_modules = []

    for ext in EXTENSIONES:
        try:
            await bot.load_extension(ext)
            logs.append(f"✅ Módulo **{ext}** cargado correctamente.")
            print(f"✅ Módulo {ext} cargado correctamente.")
            success_modules.append(ext)
        except Exception as e:
            error_msg = f"❌ Error al cargar **{ext}**:\n{e}"
            errores.append(error_msg)
            logs.append(error_msg)
            print(error_msg)

    try:
        synced = await bot.tree.sync()
        logs.append(f"✅ {len(synced)} comandos sincronizados.")
        print(f"✅ {len(synced)} comandos sincronizados.")
    except Exception as e:
        error_msg = f"❌ Error al sincronizar comandos: {e}"
        errores.append(error_msg)
        logs.append(error_msg)
        print(error_msg)

    logs_message = "\n".join(logs)

    if errores:
        logs.append("Status: Error")
        await custom_log(bot, "Error", "\n".join(errores), "❌ Resumen de inicio del bot")
        print("❌ Resumen de inicio del bot")
        for err in errores:
            print(err)
        print("Status: Error")
    else:
        logs.append("Status: Activo")
        await custom_log(bot, "Activo", "Todos los módulos cargados correctamente.", "✅ Resumen de inicio del bot")
        print("✅ Resumen de inicio del bot: Todos los módulos cargados correctamente.")
        print("Status: Activo")

    logs_message = "\n".join(logs)
    if log_message:
        await log_message.edit(content=logs_message)

    while True:
        await asyncio.sleep(60)
        print("⏳ Bot sigue vivo...")

# Ya NO hay handler global de on_message. Los Cogs funcionan de forma independiente.

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    asyncio.run(bot.start(TOKEN))
