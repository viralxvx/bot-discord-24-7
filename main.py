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
    "comandos.ver_sugerencias",
    "canales.inactividad",
    "canales.go_viral",
    "comandos.prorroga",
    "comandos.override",
    "canales.reporte_incumplimiento",
    "cogs.misc",
    "canales.anuncios",
    "canales.nuevas_funciones",
    "comandos.novedades",
    "comandos.publicar_funcion",
    "canales.soporte",  # Importante: dejar este nombre así para el get_cog
    "comandos.migrar_paneles",   # <--- PANEL PREMIUM MIGRATION
    "comandos.forzar_panel",     # <--- NUEVO: COMANDO PREMIUM INDIVIDUAL
]

log_message = None  # Mensaje embed en canal de logs
logs = []  # Lista para mensaje embed y consola Railway

def get_current_time():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

async def sincronizar_todos_los_paneles(bot):
    """
    Recorre todos los humanos del servidor y sincroniza sus paneles premium.
    """
    await bot.wait_until_ready()
    try:
        from utils.panel_embed import actualizar_panel_faltas
        import redis
        from config import REDIS_URL
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        print(f"❌ Error importando dependencias para sincronizar paneles: {e}")
        return

    for guild in bot.guilds:
        for miembro in guild.members:
            if not miembro.bot:
                try:
                    await actualizar_panel_faltas(bot, miembro)
                except Exception as e:
                    print(f"❌ Error auto-actualizando panel de {miembro.display_name}: {e}")

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

    # 🔧 FORZAMOS iniciar_soporte() tras cargar todas las extensiones
    await ejecutar_iniciar_soporte()

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

    if log_message:
        await log_message.edit(content=logs_message)

    # === Sincroniza paneles premium al iniciar (nunca más paneles viejos) ===
    print("🔄 Sincronizando TODOS los paneles premium de faltas...")
    await sincronizar_todos_los_paneles(bot)
    print("✅ Sincronización de paneles completada.")

    while True:
        await asyncio.sleep(60)
        print("⏳ Bot sigue vivo...")

# 🔁 FUNCIÓN adicional para ejecutar iniciar_soporte()
async def ejecutar_iniciar_soporte():
    await asyncio.sleep(2)  # Por si aún no terminó de cargar bien el bot
    soporte_cog = bot.get_cog("Soporte")
    if soporte_cog:
        print("[DEBUG] Ejecutando iniciar_soporte desde main.py...")
        await soporte_cog.iniciar_soporte()
    else:
        print("[ADVERTENCIA] No se encontró el cog 'Soporte'. No se pudo ejecutar iniciar_soporte().")

# === RESTRICCIÓN DE CANAL FALTAS SOLO PARA PANELES (NO HUMANOS) ===
@bot.event
async def on_message(message):
    try:
        from config import CANAL_FALTAS_ID
        if message.channel.id == CANAL_FALTAS_ID and not message.author.bot:
            await message.delete()
    except Exception:
        pass
    await bot.process_commands(message)

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    asyncio.run(bot.start(TOKEN))
