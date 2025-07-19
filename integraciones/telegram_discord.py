# integraciones/telegram_discord.py

import os
import asyncio
import discord
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv
import aiohttp

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_TELEGRAM = int(os.getenv("DISCORD_CANAL_TELEGRAM"))  # ID del canal de Discord
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_INTEGRACION")  # Usa otro token de bot solo para integración
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # Solo username, sin @ (ej: viralxvx)

# ---------- Discord a Telegram ----------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

class DiscordBridgeClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_bot = Bot(token=TELEGRAM_TOKEN, parse_mode="HTML")

    async def on_ready(self):
        print(f"[DiscordBridge] ✅ Integración activa como {self.user}")

    async def on_message(self, message):
        if message.author.bot: return
        if message.channel.id != DISCORD_CANAL_TELEGRAM: return
        text = f"<b>[Discord]</b> <i>{message.author.display_name}:</i> {message.content}"
        try:
            await self.telegram_bot.send_message(chat_id=f"@{TELEGRAM_CANAL}", text=text)
            print(f"[Discord → Telegram] {text}")
        except Exception as e:
            print(f"❌ Error enviando a Telegram: {e}")

discord_client = DiscordBridgeClient(intents=intents)

# ---------- Telegram a Discord ----------

from aiogram import Bot as TGBot, Dispatcher as TGDispatcher, types as TGTypes

tg_bot = TGBot(token=TELEGRAM_TOKEN)
tg_dp = TGDispatcher(tg_bot)

@tg_dp.channel_post_handler()
async def tg_to_discord(message: TGTypes.Message):
    # Solo canal específico
    if message.chat.username != TELEGRAM_CANAL:
        return
    text = f"[Telegram] {message.from_user.full_name if message.from_user else 'Canal'}: {message.text or '[no texto]'}"
    async with discord_client.http._HTTPClient__session.post(
        f"https://discord.com/api/v9/channels/{DISCORD_CANAL_TELEGRAM}/messages",
        json={"content": text},
        headers={
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json"
        }
    ) as resp:
        if resp.status == 200 or resp.status == 204:
            print(f"[Telegram → Discord] {text}")
        else:
            print(f"❌ Error enviando a Discord: {await resp.text()}")

async def aiogram_start():
    executor.start_polling(tg_dp, skip_updates=True)

# ---------- MAIN ----------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # Inicia ambos bots en paralelo
    loop.create_task(aiogram_start())
    loop.create_task(discord_client.start(DISCORD_TOKEN))
    loop.run_forever()
