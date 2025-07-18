import os
import sys
import logging
import redis
import re
import asyncio
from datetime import datetime, timedelta

# ==== AJUSTE DE PATH PARA IMPORTAR 'mensajes' ====
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from dotenv import load_dotenv

from mensajes import telegram as msj
from utils.mailrelay import suscribir_email

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
CANAL_USERNAME = os.getenv("TELEGRAM_CANAL", "viralxvx")
WHOP_LINK = "https://whop.com/viralxvxpremium/?store=true"
ADMIN_ID = os.getenv("ADMIN_ID")  # Soporte directo

if not TELEGRAM_TOKEN:
    raise Exception("❌ Falta TELEGRAM_TOKEN en las variables de entorno")
if not REDIS_URL:
    raise Exception("❌ Falta REDIS_URL en las variables de entorno")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

TIEMPO_RECORDATORIO_HRS = 24
TIEMPO_EXPULSION_HRS = 72

# ==== AYUDA: Detección chat privado vs grupo
def is_private(message):
    return message.chat.type == 'private'

# ==== Estado y helpers
def get_user_state(user_id):
    return redis_client.hget(f"user:telegram:{user_id}", "state") or "inicio"

def set_user_state(user_id, state):
    redis_client.hset(f"user:telegram:{user_id}", "state", state)
    redis_client.hset(f"user:telegram:{user_id}", "last_update", datetime.utcnow().isoformat())

def save_user_email(user_id, email):
    redis_client.hset(f"user:telegram:{user_id}", "email", email)
    redis_client.hset(f"user:telegram:{user_id}", "last_update", datetime.utcnow().isoformat())

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

# ==== Menú visual SOLO EN PRIVADO ====
def get_main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("❓ FAQ / Ayuda", callback_data="faq"),
        InlineKeyboardButton("🛡️ Soporte", callback_data="soporte"),
        InlineKeyboardButton("📢 Canal Oficial", url=f"https://t.me/{CANAL_USERNAME}"),
        InlineKeyboardButton("📺 Tutorial Discord", callback_data="tutorial_discord"),
        InlineKeyboardButton("💬 Grupo/Chat", url="https://t.me/+PaqyU7Z-VQQ0ZTBh"),
        InlineKeyboardButton("🧑‍💻 Mi perfil", callback_data="mi_perfil"),
        InlineKeyboardButton("🔄 Volver a empezar", callback_data="reset")
    )
    return kb

# ==== BIENVENIDA SOLO PRIVADO ====
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    if not is_private(message):
        await message.delete()
        return
    user_id = message.from_user.id
    set_user_state(user_id, "inicio")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚀 Quiero Viralizar", callback_data="quiero_viralizar"))
    await message.answer(msj.BIENVENIDA, reply_markup=kb)

# ==== BOTÓN "QUIERO VIRALIZAR" SOLO PRIVADO ====
@dp.callback_query_handler(lambda c: c.data == "quiero_viralizar")
async def handle_quiero_viralizar(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    set_user_state(user_id, "esperando_email")
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, msj.PIDE_EMAIL, reply_markup=ReplyKeyboardRemove())

# ==== EMAIL SOLO PRIVADO ====
@dp.message_handler(lambda m: is_private(m) and get_user_state(m.from_user.id) == "esperando_email")
async def recibir_email(message: types.Message):
    user_id = message.from_user.id
    email = message.text.strip()
    if not is_valid_email(email):
        await message.reply(msj.EMAIL_INVALIDO)
        return
    save_user_email(user_id, email)
    set_user_state(user_id, "esperando_canal")
    await message.reply(msj.EMAIL_OK.format(email=email))
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Ya me uní al canal", callback_data="verificar_canal"),
        InlineKeyboardButton("📢 Unirme al Canal", url=f"https://t.me/{CANAL_USERNAME}")
    )
    await message.reply(msj.PIDE_CANAL, reply_markup=kb)

# ==== VERIFICACIÓN DE CANAL SOLO PRIVADO ====
@dp.callback_query_handler(lambda c: c.data == "verificar_canal")
async def verificar_canal(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=f"@{CANAL_USERNAME}", user_id=user_id)
        if member.status not in ["member", "administrator", "creator"]:
            await bot.answer_callback_query(callback_query.id, text="⚠️ Debes unirte al canal para avanzar.", show_alert=True)
            return
    except Exception:
        await bot.answer_callback_query(callback_query.id, text="❌ No pude verificar tu membresía. Únete al canal y reintenta.", show_alert=True)
        return
    set_user_state(user_id, "whop_ok")
    await bot.answer_callback_query(callback_query.id, text="¡Perfecto! Ya eres parte del canal.", show_alert=False)
    await bot.send_message(user_id, msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_main_menu())

# ==== BLOQUEA MENSAJES FUERA DE FLUJO Y SOLO EN PRIVADO ====
@dp.message_handler(lambda m: not is_private(m) or get_user_state(m.from_user.id) not in ["esperando_email"])
async def bloquear_mensajes(message: types.Message):
    if not is_private(message):
        await message.delete()
        return
    await message.delete()
    await bot.send_message(message.from_user.id, msj.AYUDA, reply_markup=get_main_menu())

# ==== MENÚS AVANZADOS SOLO PRIVADO ====
@dp.callback_query_handler(lambda c: c.data == "faq")
async def menu_faq(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, msj.FAQ, reply_markup=get_main_menu())

@dp.callback_query_handler(lambda c: c.data == "tutorial_discord")
async def menu_tutorial(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, msj.TUTORIAL_DISCORD, reply_markup=get_main_menu())

@dp.callback_query_handler(lambda c: c.data == "soporte")
async def menu_soporte(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, msj.SOPORTE, reply_markup=get_main_menu())
    if ADMIN_ID:
        await bot.send_message(int(ADMIN_ID), f"🛡️ Usuario {callback_query.from_user.id} ha solicitado soporte.")

@dp.callback_query_handler(lambda c: c.data == "mi_perfil")
async def mi_perfil(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    email = redis_client.hget(f"user:telegram:{user_id}", "email") or "-"
    state = redis_client.hget(f"user:telegram:{user_id}", "state") or "-"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, f"📋 *Tu perfil:*\nEstado: `{state}`\nEmail: `{email}`", reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "reset")
async def resetear(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    redis_client.delete(f"user:telegram:{user_id}")
    await bot.answer_callback_query(callback_query.id, text="Tu proceso fue reiniciado.", show_alert=True)
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚀 Quiero Viralizar", callback_data="quiero_viralizar"))
    await bot.send_message(user_id, msj.BIENVENIDA, reply_markup=kb)

# ==== LIMPIEZA MENÚ EN GRUPO/CHAT (NUNCA MENÚ EN GRUPO) ====
@dp.message_handler(lambda m: m.chat.type != 'private')
async def bloquear_todo_en_grupo(message: types.Message):
    await message.delete()
    # Opcional: poner un aviso que aquí solo hay anuncios
    # await bot.send_message(message.chat.id, "Solo anuncios. Usa el bot privado para interactuar.")

# ==== LIMPIEZA AUTOMÁTICA CADA HORA ====
async def limpieza_inactivos():
    print("🔎 [LIMPIEZA] Iniciando limpieza automática...")
    now = datetime.utcnow()
    for key in redis_client.scan_iter("user:telegram:*"):
        user_id = key.split(":")[-1]
        user_state = redis_client.hget(key, "state")
        last_update = redis_client.hget(key, "last_update")
        if not last_update:
            continue
        try:
            ts = datetime.fromisoformat(last_update)
        except Exception:
            ts = now
        horas = (now - ts).total_seconds() / 3600
        # Limpieza tras 1h de inactividad (salvo premium)
        if user_state in ["inicio", "esperando_email", "esperando_canal"] and horas > 1:
            redis_client.delete(key)
            print(f"[LIMPIEZA] Usuario {user_id} eliminado tras {int(horas)}h de inactividad.")
    print("✅ [LIMPIEZA] Finalizada.")

async def schedule_limpieza():
    while True:
        await limpieza_inactivos()
        await asyncio.sleep(3600)  # 1 hora

if __name__ == "__main__":
    print("✅ Bot de Telegram VXbot FINAL listo y corriendo.")
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_limpieza())
    executor.start_polling(dp, skip_updates=True)
