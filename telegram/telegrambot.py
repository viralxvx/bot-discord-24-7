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
    ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
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
CHAT_LINK = os.getenv("TELEGRAM_CHAT", "https://t.me/+PaqyU7Z-VQQ0ZTBh")
DISCORD_LINK = os.getenv("DISCORD_LINK", "https://discord.gg/viralxvx")
WHOP_LINK = "https://whop.com/viralxvxpremium/?store=true"
ADMIN_ID = os.getenv("ADMIN_ID")  # Solo 1 admin para soporte

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

# === MENU FIJO ===
def get_menu_fijo():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("❓ FAQ / Ayuda"), KeyboardButton("🛡️ Soporte")],
            [KeyboardButton("📢 Canal Oficial"), KeyboardButton("📺 Tutorial Discord")],
            [KeyboardButton("💬 Grupo/Chat"), KeyboardButton("🎫 Acceso Discord")],
            [KeyboardButton("👤 Mi perfil"), KeyboardButton("🔄 Volver a empezar")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# === ESTADOS Y HELPERS ===
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

async def limpiar_historial_usuario(user_id):
    # Elimina TODO el historial anterior del usuario y deja solo bienvenida/menu
    try:
        async for msg in bot.iter_history(user_id):
            try:
                await bot.delete_message(user_id, msg.message_id)
            except: pass
    except Exception as e:
        print(f"[WARN] No se pudo limpiar historial para {user_id}: {e}")

# === HANDLERS DE BOT PRIVADO (NO GRUPOS/CHANNELS) ===

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await limpiar_historial_usuario(user_id)
    set_user_state(user_id, "inicio")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🚀 Quiero Viralizar"))
    await message.answer(msj.BIENVENIDA, reply_markup=kb)

@dp.message_handler(lambda m: m.text and "quiero viralizar" in m.text.lower())
async def arranca_viralizar(message: types.Message):
    user_id = message.from_user.id
    set_user_state(user_id, "esperando_email")
    await message.answer(msj.PIDE_EMAIL, reply_markup=get_menu_fijo())

@dp.message_handler(lambda message: get_user_state(message.from_user.id) == "esperando_email")
async def recibir_email(message: types.Message):
    user_id = message.from_user.id
    email = message.text.strip()
    if not is_valid_email(email):
        await message.reply(msj.EMAIL_INVALIDO, reply_markup=get_menu_fijo())
        return
    save_user_email(user_id, email)
    set_user_state(user_id, "esperando_canal")
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Ya me uní al canal", callback_data="verificar_canal"),
        InlineKeyboardButton("📢 Unirme al Canal", url=f"https://t.me/{CANAL_USERNAME}")
    )
    await message.reply(msj.EMAIL_OK.format(email=email), reply_markup=get_menu_fijo())
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
    await bot.send_message(user_id, msj.WHOP_ENTREGA.format(whop_link=WHOP_LINK), reply_markup=get_menu_fijo())

# ==== MENU EXTENDIDO ====

@dp.message_handler(lambda m: m.text and "faq" in m.text.lower())
async def handler_faq(message: types.Message):
    await message.answer(msj.FAQ, reply_markup=get_menu_fijo())

@dp.message_handler(lambda m: m.text and "soporte" in m.text.lower())
async def handler_soporte(message: types.Message):
    await message.answer(msj.SOPORTE, reply_markup=get_menu_fijo())
    if ADMIN_ID:
        await bot.send_message(int(ADMIN_ID), f"🛡️ Usuario [{message.from_user.id}](tg://user?id={message.from_user.id}) ha solicitado soporte.")

@dp.message_handler(lambda m: m.text and "tutorial" in m.text.lower())
async def handler_tutorial(message: types.Message):
    await message.answer(msj.TUTORIAL_DISCORD, reply_markup=get_menu_fijo())

@dp.message_handler(lambda m: m.text and "grupo" in m.text.lower())
async def handler_grupo(message: types.Message):
    await message.answer(f"Entra a nuestro grupo/chat aquí: {CHAT_LINK}", reply_markup=get_menu_fijo())

@dp.message_handler(lambda m: m.text and "canal" in m.text.lower())
async def handler_canal(message: types.Message):
    await message.answer(f"Canal oficial de novedades: https://t.me/{CANAL_USERNAME}", reply_markup=get_menu_fijo())

@dp.message_handler(lambda m: m.text and "discord" in m.text.lower())
async def handler_discord(message: types.Message):
    await message.answer(f"Entra a Discord: {DISCORD_LINK}", reply_markup=get_menu_fijo())

@dp.message_handler(lambda m: m.text and "mi perfil" in m.text.lower())
async def handler_perfil(message: types.Message):
    email = get_user_email(message.from_user.id)
    state = get_user_state(message.from_user.id)
    await message.answer(f"👤 Tu perfil:\n\nEstado: {state}\nEmail: {email or 'No registrado'}", reply_markup=get_menu_fijo())

@dp.message_handler(lambda m: m.text and "volver a empezar" in m.text.lower())
async def handler_reset(message: types.Message):
    await limpiar_historial_usuario(message.from_user.id)
    set_user_state(message.from_user.id, "inicio")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🚀 Quiero Viralizar"))
    await message.answer(msj.BIENVENIDA, reply_markup=kb)

# === LIMPIEZA AUTOMÁTICA Y /inactivos ADMIN ===
async def limpieza_inactivos():
    print("🔎 [LIMPIEZA] Iniciando limpieza automática...")
    now = datetime.utcnow()
    count_expulsados, count_recordados = 0, 0
    for key in redis_client.scan_iter("user:telegram:*"):
        user_id = key.split(":")[-1]
        user_state = redis_client.hget(key, "state")
        email = redis_client.hget(key, "email") or None
        last_update = redis_client.hget(key, "last_update")
        if not last_update:
            continue
        try:
            ts = datetime.fromisoformat(last_update)
        except:
            ts = now
        horas = (now - ts).total_seconds() / 3600
        # Solo limpiar atascados, no premium
        if user_state in ["inicio", "esperando_email", "esperando_canal"]:
            if horas > TIEMPO_EXPULSION_HRS and not email:
                try:
                    await bot.send_message(
                        user_id, 
                        "⚠️ No completaste tu registro y serás eliminado por inactividad.\nSi fue un error, vuelve a iniciar escribiendo /start."
                    )
                except: pass
                redis_client.delete(key)
                count_expulsados += 1
                print(f"[EXPULSADO] Usuario {user_id} eliminado por inactividad ({int(horas)}h).")
            elif email and horas > TIEMPO_RECORDATORIO_HRS:
                kb = ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(KeyboardButton("🔄 Volver a empezar"))
                try:
                    await bot.send_message(
                        user_id,
                        "👋 Aún no completaste tu acceso premium.\nPulsa abajo para reiniciar el proceso o pide ayuda en Soporte.",
                        reply_markup=kb
                    )
                    redis_client.hset(key, "last_update", now.isoformat())
                    count_recordados += 1
                    print(f"[RECORDATORIO] Usuario {user_id} recordado por inactividad ({int(horas)}h).")
                except: pass
    print(f"✅ [LIMPIEZA] Finalizada. Expulsados: {count_expulsados} | Recordados: {count_recordados}")

async def schedule_limpieza():
    while True:
        await limpieza_inactivos()
        await asyncio.sleep(TIEMPO_RECORDATORIO_HRS * 3600)  # 24h

@dp.message_handler(commands=["inactivos"])
async def cmd_inactivos(message: types.Message):
    if not ADMIN_ID or str(message.from_user.id) != str(ADMIN_ID):
        return
    now = datetime.utcnow()
    res = []
    for key in redis_client.scan_iter("user:telegram:*"):
        user_id = key.split(":")[-1]
        state = redis_client.hget(key, "state")
        email = redis_client.hget(key, "email") or "-"
        last_update = redis_client.hget(key, "last_update") or "-"
        res.append(f"ID: {user_id} | Estado: {state} | Email: {email} | Último movimiento: {last_update}")
    if not res:
        await message.reply("No hay inactivos encontrados.")
    else:
        await message.reply("\n".join(res[:50]))

if __name__ == "__main__":
    print("✅ Bot de Telegram VXbot FINAL listo y corriendo.")
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_limpieza())
    executor.start_polling(dp, skip_updates=True)
