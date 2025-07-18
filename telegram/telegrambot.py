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
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from dotenv import load_dotenv

from mensajes import telegram as msj
from utils.mailrelay import suscribir_email

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
CANAL_USERNAME = os.getenv("TELEGRAM_CANAL", "viralxvx")   # Solo el username (sin @ ni link)
CHAT_LINK = os.getenv("TELEGRAM_CHAT", "https://t.me/+PaqyU7Z-VQQ0ZTBh")
WHOP_LINK = "https://whop.com/viralxvxpremium/?store=true"
ADMIN_ID = os.getenv("ADMIN_ID")  # Si quieres soporte directo

if not TELEGRAM_TOKEN:
    raise Exception("❌ Falta TELEGRAM_TOKEN en las variables de entorno")
if not REDIS_URL:
    raise Exception("❌ Falta REDIS_URL en las variables de entorno")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# === CONFIGURACIÓN DE LIMPIEZA DE INACTIVOS ===
TIEMPO_EXPULSION_HRS = 1      # Cambia a 1 hora para pruebas. Ajusta si lo quieres más.

# === Estados y helpers
def get_user_state(user_id):
    return redis_client.hget(f"user:telegram:{user_id}", "state") or "inicio"

def set_user_state(user_id, state):
    redis_client.hset(f"user:telegram:{user_id}", "state", state)
    redis_client.hset(f"user:telegram:{user_id}", "last_update", datetime.utcnow().isoformat())

def save_user_email(user_id, email):
    redis_client.hset(f"user:telegram:{user_id}", "email", email)
    redis_client.hset(f"user:telegram:{user_id}", "last_update", datetime.utcnow().isoformat())

def get_user_email(user_id):
    return redis_client.hget(f"user:telegram:{user_id}", "email") or ""

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

def reset_usuario(user_id):
    redis_client.delete(f"user:telegram:{user_id}")

# === MENÚ EXTENDIDO SOLO EN PRIVADO ===
def get_main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("❓ FAQ / Ayuda", callback_data="faq"),
        InlineKeyboardButton("📺 Tutorial Discord", callback_data="tutorial_discord"),
        InlineKeyboardButton("📢 Canal Oficial", url=f"https://t.me/{CANAL_USERNAME}"),
        InlineKeyboardButton("💬 Grupo/Chat", url=CHAT_LINK),
        InlineKeyboardButton("💳 Acceso Discord", url=WHOP_LINK),
        InlineKeyboardButton("👤 Mi perfil", callback_data="perfil"),
        InlineKeyboardButton("🛡️ Soporte", callback_data="soporte"),
        InlineKeyboardButton("🔁 Volver a empezar", callback_data="reiniciar")
    )
    return kb

# === SOLO RESPONDE EN PRIVADO ===
@dp.message_handler(lambda message: message.chat.type != "private")
async def solo_privado(message: types.Message):
    try:
        await message.delete()
    except:
        pass
    try:
        await bot.send_message(message.from_user.id, "🚫 Solo puedes usar el menú en el chat privado del bot.\n\nEscríbeme aquí 👉 @VXtelegram_bot")
    except:
        pass

# === BIENVENIDA ===
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    reset_usuario(user_id)
    set_user_state(user_id, "inicio")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚀 Quiero Viralizar", callback_data="quiero_viralizar"))
    await message.answer(msj.BIENVENIDA, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "reiniciar")
async def reiniciar_proceso(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    reset_usuario(user_id)
    set_user_state(user_id, "inicio")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚀 Quiero Viralizar", callback_data="quiero_viralizar"))
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, msj.BIENVENIDA, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "quiero_viralizar")
async def handle_quiero_viralizar(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    set_user_state(user_id, "esperando_email")
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, msj.PIDE_EMAIL, reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda message: get_user_state(message.from_user.id) == "esperando_email")
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

@dp.callback_query_handler(lambda c: c.data == "verificar_canal")
async def verificar_canal(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=f"@{CANAL_USERNAME}", user_id=user_id)
        if member.status not in ["member", "administrator", "creator"]:
            await bot.answer_callback_query(callback_query.id, text="⚠️ Debes unirte al canal para avanzar.", show_alert=True)
            return
    except Exception as e:
        await bot.answer_callback_query(callback_query.id, text="❌ No pude verificar tu membresía. Únete al canal y reintenta.", show_alert=True)
        return
    set_user_state(user_id, "whop_ok")
    await bot.answer_callback_query(callback_query.id, text="¡Perfecto! Ya eres parte del canal.", show_alert=False)
    await bot.send_message(user_id, msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_main_menu())

# MENÚ EXTENDIDO
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

@dp.callback_query_handler(lambda c: c.data == "perfil")
async def mi_perfil(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    email = get_user_email(user_id)
    state = get_user_state(user_id)
    perfil_txt = f"👤 *Tu perfil VX*\n\nEstado: `{state}`\nEmail: `{email}`" if email else "No tienes email registrado aún."
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, perfil_txt, reply_markup=get_main_menu())

# Bloquear mensajes fuera del flujo
@dp.message_handler(lambda message: get_user_state(message.from_user.id) not in ["esperando_email"])
async def bloquear_mensajes(message: types.Message):
    await message.delete()
    await bot.send_message(message.from_user.id, msj.AYUDA, reply_markup=get_main_menu())

# === LIMPIEZA AUTOMÁTICA ===
async def limpieza_inactivos():
    print("🔎 [LIMPIEZA] Buscando inactivos para limpiar...")
    now = datetime.utcnow()
    for key in redis_client.scan_iter("user:telegram:*"):
        user_id = key.split(":")[-1]
        last_update = redis_client.hget(key, "last_update")
        if not last_update:
            continue
        try:
            ts = datetime.fromisoformat(last_update)
        except:
            ts = now
        horas = (now - ts).total_seconds() / 3600
        if horas > TIEMPO_EXPULSION_HRS:
            # Limpiar usuario
            print(f"[LIMPIADO] Usuario {user_id} inactivo {int(horas)}h, limpiando registro y menú.")
            reset_usuario(user_id)
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🚀 Quiero Viralizar", callback_data="quiero_viralizar"))
            try:
                await bot.send_message(int(user_id), msj.BIENVENIDA, reply_markup=kb)
            except Exception as e:
                print(f"[WARN] No pude notificar a {user_id}: {e}")

async def schedule_limpieza():
    while True:
        await limpieza_inactivos()
        await asyncio.sleep(10 * 60)  # Cada 10 min, puedes cambiar

if __name__ == "__main__":
    print("✅ Bot de Telegram VXbot FINAL listo y corriendo.")
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_limpieza())  # Arranca limpieza automática
    executor.start_polling(dp, skip_updates=True)
