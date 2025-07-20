# main.py

import discord
from discord.ext import commands
from config import DISCORD_TOKEN, GUILD_ID
from comandos import idea_viral

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

class VXBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        await self.add_cog(idea_viral.IdeaViral(self))
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("🤖 Asistente de hilos virales activo y comandos sincronizados.")

bot = VXBot()

@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user}")

bot.run(DISCORD_TOKEN)
