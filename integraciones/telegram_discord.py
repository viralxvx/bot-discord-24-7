# integraciones/telegram_discord.py

import os
import asyncio
import discord
import aiohttp

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_TELEGRAM = int(os.getenv("DISCORD_CANAL_TELEGRAM"))  # Debes tener el ID
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # Solo el username sin @

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Integración activa como {bot.user}")

@bot.event
async def on_message(message):
    # No repitas mensajes de bots
    if message.author.bot:
        return
    # Solo replica los mensajes del canal configurado
    if message.channel.id != DISCORD_CANAL_TELEGRAM:
        return

    text = f"[Discord] {message.author.display_name}: {message.content}"
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": f"@{TELEGRAM_CANAL}",
            "text": text
        }
        async with session.post(url, data=payload) as resp:
            if resp.status == 200:
                print(f"✅ Mensaje enviado a Telegram: {text}")
            else:
                print(f"❌ Error al enviar mensaje a Telegram: {await resp.text()}")

if __name__ == "__main__":
    print("🔗 Integración Discord → Telegram corriendo...")
    asyncio.run(bot.start(DISCORD_TOKEN))
