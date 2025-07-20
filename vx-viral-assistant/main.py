# main.py

import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, GUILD_ID

class VXBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            await self.load_extension('comandos.idea_viral')
            print("✅ Extensión idea_viral cargada")
        except Exception as e:
            print(f"❌ Error cargando idea_viral: {e}")
            return

        try:
            guild = discord.Object(id=GUILD_ID)
            synced = await self.tree.sync(guild=guild)
            print(f"🔁 Comandos sincronizados en GUILD {GUILD_ID}: {[cmd.name for cmd in synced]}")
        except Exception as e:
            print(f"❌ Error sincronizando comandos: {e}")

    async def on_ready(self):
        print(f"✅ Conectado como {self.user}")

async def main():
    bot = VXBot()
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
