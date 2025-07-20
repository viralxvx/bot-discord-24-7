# main.py

import discord
from discord.ext import commands
from config import DISCORD_TOKEN
import asyncio

class VXBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # elimina el warning y permite registrar interacciones si lo usas en futuro
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Cargar la extensión del comando idea_viral
        try:
            await self.load_extension('comandos.idea_viral')
            print("✅ Extensión idea_viral cargada")
        except Exception as e:
            print(f"❌ Error cargando idea_viral: {e}")
            return

        # Mostrar comandos cargados antes de sincronizar
        print(f"📋 Comandos en el árbol antes de sync: {[cmd.name for cmd in self.tree.get_commands()]}")

        # Sincronizar los comandos (sin borrar los de otros servicios)
        try:
            synced = await self.tree.sync()
            print(f"🔁 Comandos sincronizados: {[cmd.name for cmd in synced]}")
            print(f"📊 Total comandos sincronizados: {len(synced)}")
        except Exception as e:
            print(f"❌ Error sincronizando comandos: {e}")

    async def on_ready(self):
        print(f"✅ Conectado como {self.user}")
        print(f"🆔 ID del bot: {self.user.id}")

# Ejecutar el bot de forma segura
async def main():
    bot = VXBot()
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente")
    except Exception as e:
        print(f"❌ Error iniciando el bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
