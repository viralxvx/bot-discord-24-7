import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN
from canales.go_viral import setup as go_viral_setup

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ✅ Registrar eventos ANTES de iniciar el bot
go_viral_setup(bot)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f'Bot conectado como {bot.user}')
    
    # ✅ Enviar mensaje al canal de logs (ID: 1388347584061374514)
    canal_logs = bot.get_channel(1388347584061374514)
    if canal_logs:
        try:
            await canal_logs.send(f"🟢 **Bot conectado como `{bot.user.name}` y listo para funcionar.**")
        except Exception as e:
            print(f"Error al enviar al canal de logs: {e}")

async def main():
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
