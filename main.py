import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONES = [
    "canales.presentate",
    "canales.normas_generales",
    "canales.faltas",
    "comandos"  # Este módulo cargará estado.py y estadisticas.py
]

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

    for ext in EXTENSIONES:
        try:
            await bot.load_extension(ext)
            print(f"✅ Módulo cargado: {ext}")
        except Exception as e:
            print(f"❌ Error al cargar {ext}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} comandos sincronizados.")
    except Exception as e:
        print(f"❌ Error al sincronizar comandos: {e}")

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
