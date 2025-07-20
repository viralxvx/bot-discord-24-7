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
        # Cargar comando
        await self.add_cog(idea_viral.IdeaViral(self))
        print("✅ Comando /idea_viral cargado correctamente.")

        # Borrar comandos antiguos del servidor (previene conflictos)
        try:
            self.tree.clear_commands(guild=discord.Object(id=GUILD_ID))
            print("🧹 Comandos antiguos eliminados.")
        except Exception as e:
            print(f"❌ Error al limpiar comandos antiguos: {e}")

        # Sincronizar comandos nuevos
        try:
            synced = await self.tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"🔁 Comandos sincronizados: {[cmd.name for cmd in synced]}")
        except Exception as e:
            print(f"❌ Error al sincronizar comandos: {e}")

bot = VXBot()

@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user}")

bot.run(DISCORD_TOKEN)
