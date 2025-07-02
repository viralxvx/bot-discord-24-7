import discord
from discord.ext import commands
import os
import asyncio
from config import TOKEN, GUILD_ID

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True  # Requerido para borrar mensajes no bot en normas-generales

bot = commands.Bot(command_prefix="!", intents=intents)

# Al estar listo, muestra conexión y sincroniza comandos slash (si los agregas más adelante)
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🔁 {len(synced)} comandos sincronizados.")
    except Exception as e:
        print(f"❌ Error al sincronizar comandos: {e}")

# Cargar todos los módulos aquí
async def load_extensions():
    await bot.load_extension("canales.presentate")
    await bot.load_extension("canales.normas_generales")

# Iniciar el bot
async def main():
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
