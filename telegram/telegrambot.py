# telegram/telegrambot.py

import os
import sys
import logging
import redis

# ====== CORRECCIÓN DE PYTHONPATH para Railway/imports ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# ===========================================================

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from dotenv import load_dotenv

from mensajes import telegram as msj

# Carga variables de entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

if not TELEGRAM_TOKEN:
    raise Exception("❌ Falta TELEGRAM_TOKEN en las variables de entorno")
if not REDIS_URL:
    raise Exception("❌ Falta REDIS_URL en las variables de entorno")

# Configura Redis y logs
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
logging.basicConfig(level=logging.INFO)

# Inicializa bot
bot = Bot(token=TELEGRAM_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=["start", "ayuda", "help"])
async def send_welcome(message: types.Message):
    print(f"[ONBOARDING] Usuario {message.from_user.id} inició /start")
    await message.reply(msj.BIENVENIDA)

@dp.message_handler(lambda message: message.text and "quiero viralizar" in message.text.lower())
async def flujo_onboarding(message: types.Message):
    user_id = message.from_user.id
    print(f"[ONBOARDING] Usuario {user_id} escribió 'Quiero Viralizar'")
    redis_client.hset(f"user:telegram:{user_id}", "estado", "iniciado")
    await message.reply("¡Perfecto! Pronto recibirás instrucciones para continuar con el proceso.")

@dp.message_handler()
async def fallback(message: types.Message):
    print(f"[MENSAJE] Usuario {message.from_user.id}: {message.text}")
    await message.reply(msj.AYUDA)

if __name__ == "__main__":
    print("✅ Bot de Telegram VXbot iniciado correctamente.")
    executor.start_polling(dp, skip_updates=True)
