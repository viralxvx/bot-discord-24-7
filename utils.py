import datetime
import discord
import asyncio

async def registrar_log(bot: discord.Client, mensaje: str, categoria: str = "general"):
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{ahora}][{categoria.upper()}] {mensaje}"

    for guild in bot.guilds:
        canal_logs = discord.utils.get(guild.text_channels, name="📝logs")
        if canal_logs:
            try:
                await canal_logs.send(log_msg)
            except Exception as e:
                print(f"Error enviando log al canal 📝logs: {e}")
            break
    else:
        print(f"No se encontró canal 📝logs en ningún servidor.")

    print(log_msg)


# Guardar estado (ejemplo simplificado; en producción conecta con Redis o DB)
def save_state(key, value):
    print(f"Guardando estado: {key} = {value}")
    # Aquí agregas la lógica real para guardar estado (Redis, archivo, etc)


# Actualizar mensaje de faltas (ejemplo para enviar mensaje en canal)
async def actualizar_mensaje_faltas(channel: discord.TextChannel, user: discord.User, faltas_count: int):
    mensaje = f"Usuario {user.name} tiene {faltas_count} faltas."
    await channel.send(mensaje)
