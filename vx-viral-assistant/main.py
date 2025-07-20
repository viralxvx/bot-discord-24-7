# main.py o tu archivo principal del bot
import discord
from discord.ext import commands
import asyncio
import os
from config import DISCORD_TOKEN

# Configurar intents (incluyendo message content intent)
intents = discord.Intents.default()
intents.message_content = True  # Añadir esto para eliminar el warning

class VXBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        # Cargar comandos
        try:
            await self.load_extension('comandos.idea_viral')
        except Exception as e:
            print(f"❌ Error cargando idea_viral: {e}")
        
        # Limpiar comandos antiguos
        self.tree.clear_commands(guild=None)
        print("🧹 Comandos antiguos eliminados.")
        
        # Sincronizar comandos slash
        try:
            synced = await self.tree.sync()
            print(f"🔁 Comandos sincronizados: {[cmd.name for cmd in synced]}")
        except Exception as e:
            print(f"❌ Error sincronizando comandos: {e}")
    
    async def on_ready(self):
        print(f"✅ Conectado como {self.user}")
        print(f"🆔 ID del bot: {self.user.id}")

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
