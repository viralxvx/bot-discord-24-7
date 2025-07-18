# telegram/telegrambot.py

import os
import sys
import logging
import redis
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from dotenv import load_dotenv

from mensajes import telegram as msj
from utils.mailrelay import suscribir_email

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
CANAL_LINK = os.getenv("TELEGRAM_CANAL", "https://t.me/viralxvx")
CHAT_LINK = os.getenv("TELEGRAM_CHAT", "https://t.me/+PaqyU7Z-VQQ0ZTBh")
WHOP_LINK = "https://whop.com/viralxvxpremium/?store=true"

if not TELEGRAM_TOKEN:
    raise Exception("❌ Falta TELEGRAM_TOKEN en las variables de entorno")
if not REDIS_URL:
    raise Exception("❌ Falta REDIS_URL en las variables de entorno")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

def get_user_state(user_id):
    return redis_client.hget(f"user:telegram:{user_id}", "state") or "inicio"

def set_user_state(user_id, state):
    redis_client.hset(f"user:telegram:{user_id}", "state", state)

def save_user_email(user_id, email):
    redis_client.hset(f"user:telegram:{user_id}", "email", email)

def get_user_email(user_id):
    return redis_client.hget(f"user:telegram:{user_id}", "email") or ""

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

def get_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❓ FAQ / Ayuda"),
           KeyboardButton("📺 Tutorial Discord"),
           KeyboardButton("📢 Canal Oficial"),
           KeyboardButton("💬 Grupo/Chat"),
           KeyboardButton("🛡️ Soporte"))
    return kb

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    set_user_state(user_id, "inicio")
    print(f"[ONBOARDING] Usuario {user_id} inició /start")
    await message.reply(msj.BIENVENIDA, reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda message: message.text and "quiero viralizar" in message.text.lower())
async def flujo_onboarding(message: types.Message):
    user_id = message.from_user.id
    state = get_user_state(user_id)
    print(f"[ONBOARDING] Usuario {user_id} escribió 'Quiero Viralizar' | Estado: {state}")

    if state == "whop_ok":
        await message.reply(msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_main_menu())
        return
    if state == "mailrelay_ok":
        await message.reply(msj.MAILRELAY_OK, reply_markup=get_main_menu())
        await message.reply(msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_main_menu())
        set_user_state(user_id, "whop_ok")
        return
    if state == "email_ok":
        await message.reply(msj.YA_REGISTRADO, reply_markup=get_main_menu())
        return

    set_user_state(user_id, "esperando_email")
    await message.reply(msj.PIDE_EMAIL, reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda message: get_user_state(message.from_user.id) == "esperando_email")
async def recibir_email(message: types.Message):
    user_id = message.from_user.id
    email = message.text.strip()
    print(f"[ONBOARDING] Usuario {user_id} envió email: {email}")

    if not is_valid_email(email):
        await message.reply(msj.EMAIL_INVALIDO)
        return

    save_user_email(user_id, email)
    print(f"[ONBOARDING] Email válido guardado para usuario {user_id}: {email}")
    await message.reply("Validando tu correo en la plataforma...")

    ok, resp = suscribir_email(email)
    if ok:
        set_user_state(user_id, "mailrelay_ok")
        await message.reply(msj.MAILRELAY_OK, reply_markup=get_main_menu())
        await message.reply(msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_main_menu())
        set_user_state(user_id, "whop_ok")
    else:
        print(f"[MAILRELAY] Error para usuario {user_id}: {resp}")
        if resp == "YA_EXISTE":
            await message.reply(msj.MAILRELAY_YA_EXISTE, reply_markup=get_main_menu())
            await message.reply(msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_main_menu())
            set_user_state(user_id, "whop_ok")
        else:
            await message.reply(msj.MAILRELAY_ERROR, reply_markup=ReplyKeyboardRemove())
            set_user_state(user_id, "email_ok")  # Permite volver a intentar si usuario escribe de nuevo

# -- MENÚ AVANZADO Y FAQ --
@dp.message_handler(lambda message: message.text == "❓ FAQ / Ayuda")
async def menu_faq(message: types.Message):
    await message.reply(msj.FAQ, reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "📢 Canal Oficial")
async def menu_canal(message: types.Message):
    await message.reply(f"Entra a nuestro canal oficial: {CANAL_LINK}", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "💬 Grupo/Chat")
async def menu_chat(message: types.Message):
    await message.reply(f"Únete al chat de la comunidad aquí: {CHAT_LINK}", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "📺 Tutorial Discord")
async def menu_tutorial(message: types.Message):
    await message.reply(msj.TUTORIAL_DISCORD, reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "🛡️ Soporte")
async def menu_soporte(message: types.Message):
    await message.reply(msj.SOPORTE, reply_markup=get_main_menu())

@dp.message_handler(lambda message: get_user_state(message.from_user.id) == "whop_ok")
async def menu_registrado(message: types.Message):
    await message.reply(msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_main_menu())

@dp.message_handler()
async def fallback(message: types.Message):
    print(f"[MENSAJE] Usuario {message.from_user.id}: {message.text}")
    await message.reply(msj.AYUDA, reply_markup=get_main_menu())

if __name__ == "__main__":
    print("✅ Bot de Telegram VXbot FASE 3 iniciado correctamente.")
    executor.start_polling(dp, skip_updates=True)
