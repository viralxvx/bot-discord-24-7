# integraciones/telegram_discord.py

import os
import asyncio
from aiogram import Bot as TGBot, Dispatcher as TGDispatcher, types as tg_types
from discord.ext import commands
import discord
import aiohttp

# === VARIABLES DE ENTORNO ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_TELEGRAM = int(os.getenv("DISCORD_CANAL_TELEGRAM"))  # <-- debes agregarlo en Railway con el ID
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # Username SIN arroba, ej: viralxvx

# === --- TELEGRAM A DISCORD --- ===

# Telegram bot
tg_bot = TGBot(token=TELEGRAM_TOKEN)
tg_dp = TGDispatcher(tg_bot)

# Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_bot = commands.Bot(command_prefix="!", intents=intents)

async def telegram_to_discord():
    @tg_dp.message_handler()
    async def handle_telegram_msg(message: tg_types.Message):
        # Solo mensajes de texto (puedes ampliar a fotos, docs, etc)
        if message.chat.type in ["group", "supergroup", "channel", "private"]:
            text = f"[TG] {message.from_user.full_name}: {message.text}"
            channel = discord_bot.get_channel(DISCORD_CANAL_TELEGRAM)
            if channel:
                await channel.send(text)

    await tg_dp.start_polling()

# === --- DISCORD A TELEGRAM --- ===

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return  # No repitas mensajes de bots (ni el tuyo)
    if message.channel.id != DISCORD_CANAL_TELEGRAM:
        return  # Solo replica del canal configurado

    # Envía a Telegram (como mensaje sencillo)
    text = f"[Discord] {message.author.display_name}: {message.content}"
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": f"@{TELEGRAM_CANAL}",  # Usa el username del canal/chat Telegram, SIN @
            "text": text
        }
        await session.post(url, data=payload)

    await discord_bot.process_commands(message)

# === ARRANQUE ===

async def main():
    # Arranca ambos bots en paralelo
    await asyncio.gather(
        discord_bot.start(DISCORD_TOKEN),
        telegram_to_discord(),
    )

if __name__ == "__main__":
    print("🔗 Sincronización Telegram <-> Discord corriendo...")
    asyncio.run(main())
