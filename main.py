import os
import discord
from discord.ext import commands
import asyncio

from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "canales.presentate",
    "canales.normas_generales",
    "canales.faltas",
    "canales.comandos",
    "canales.inactividad",
    "canales.soporte_prorroga",
    "canales.go_viral",
    "canales.reporte_incumplimiento",
    "comandos.prorroga",
    "comandos.override",
]

async def load_cogs():
    for ext in COGS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Módulo {ext} cargado correctamente.")
        except Exception as e:
            print(f"❌ Error al cargar {ext}: {e}")

async def main():
    await load_cogs()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
