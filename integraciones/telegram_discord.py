# integraciones/telegram_discord.py

import os
import asyncio
import logging
import discord
from discord.ext import commands
from aiogram import Bot as TGBot, Dispatcher as TGDispatcher, types as tg_types
from aiogram.utils.exceptions import BotBlocked

# ========== CONFIG ==========
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_TELEGRAM = int(os.getenv("DISCORD_CANAL_TELEGRAM"))  # numérico
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # username público, sin @

if not all([DISCORD_TOKEN, DISCORD_CANAL_TELEGRAM, TELEGRAM_TOKEN, TELEGRAM_CANAL]):
    raise Exception("❌ Faltan variables de entorno en el microservicio de integración.")

logging.basicConfig(level=logging.INFO)

# ========== TELEGRAM SETUP ==========
tg_bot = TGBot(token=TELEGRAM_TOKEN)
tg_dp = TGDispatcher(tg_bot)

# ========== DISCORD SETUP ==========
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_bot = commands.Bot(command_prefix="!", intents=intents)

# ---- DISCORD a TELEGRAM ----
@discord_bot.event
async def on_ready():
    print(f"✅ Discord ↔ Telegram integración activa como {discord_bot.user}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id == DISCORD_CANAL_TELEGRAM:
        text = f"[Discord] {message.author.display_name}: {message.content}"
        try:
            await tg_bot.send_message(chat_id=f"@{TELEGRAM_CANAL}", text=text)
            print(f"✅ Discord → Telegram: {text}")
        except Exception as e:
            print(f"❌ Error enviando a Telegram: {e}")
    await discord_bot.process_commands(message)

# ---- TELEGRAM a DISCORD ----
@tg_dp.message_handler(lambda m: m.chat.type in ["channel", "supergroup", "group", "private"])
async def handle_telegram_msg(message: tg_types.Message):
    if message.text:
        text = f"[TG] {message.from_user.full_name}: {message.text}" if message.from_user else f"[TG]: {message.text}"
        try:
            channel = discord_bot.get_channel(DISCORD_CANAL_TELEGRAM)
            if channel:
                await channel.send(text)
                print(f"✅ Telegram → Discord: {text}")
            else:
                print("❌ Canal de Discord no encontrado.")
        except Exception as e:
            print(f"❌ Error enviando a Discord: {e}")

# ========== ARRANQUE ==========
async def main():
    await asyncio.gather(
        discord_bot.start(DISCORD_TOKEN),
        tg_dp.start_polling()
    )

if __name__ == "__main__":
    print("🔗 Integración Discord ↔ Telegram corriendo...")
    asyncio.run(main())
