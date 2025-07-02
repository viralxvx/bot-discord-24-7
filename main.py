import discord
from discord.ext import commands
import os
from config import TOKEN, GUILD_ID
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cargar los cogs
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🔁 {len(synced)} comandos sincronizados.")
    except Exception as e:
        print(f"❌ Error al sincronizar comandos: {e}")

@bot.event
async def on_member_join(member):
    from canales.presentate import enviar_bienvenida
    await enviar_bienvenida(member, bot)

# Cargar extensiones manualmente
async def load_extensions():
    await bot.load_extension("canales.presentate")

async def main():
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
