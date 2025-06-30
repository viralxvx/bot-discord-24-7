import datetime
import discord
import asyncio

async def registrar_log(bot: discord.Client, mensaje: str, categoria: str = "general"):
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{ahora}][{categoria.upper()}] {mensaje}"

    # Buscar el canal llamado "📝logs" en todos los servidores donde está el bot
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

    # También imprime en consola
    print(log_msg)
