import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import aiohttp

TELEGRAM_TOKEN_INTEGRACION = os.getenv("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # Username, ej: viralxvx
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Pon tu webhook aquí

if not TELEGRAM_TOKEN_INTEGRACION or not TELEGRAM_CANAL or not DISCORD_WEBHOOK_URL:
    raise Exception("❌ Faltan variables para la integración Telegram → Discord (webhook)")

tg_bot = Bot(token=TELEGRAM_TOKEN_INTEGRACION)
tg_dp = Dispatcher(tg_bot)

@tg_dp.message_handler()
async def handle_telegram_msg(message: types.Message):
    # Solo canal configurado (no grupos, no privados)
    if message.chat.type == "channel" and message.chat.username and message.chat.username.lower() == TELEGRAM_CANAL.lower():
        text = f"**[Telegram]**\n{message.text}"
        async with aiohttp.ClientSession() as session:
            payload = {"content": text}
            async with session.post(DISCORD_WEBHOOK_URL, json=payload) as resp:
                if resp.status == 204:
                    print(f"✅ Telegram → Discord (webhook): {text}")
                else:
                    print(f"❌ Error webhook Discord: {await resp.text()}")
    else:
        print(f"⚠️ Mensaje ignorado de chat {message.chat.id} tipo {message.chat.type}")

if __name__ == "__main__":
    print("🔗 Telegram → Discord (webhook) corriendo...")
    executor.start_polling(tg_dp, skip_updates=True)
