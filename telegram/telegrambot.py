import os
import sys
import logging
import redis
import re
import asyncio
from datetime import datetime

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
CANAL_USERNAME = os.getenv("TELEGRAM_CANAL", "viralxvx")
WHOP_LINK = "https://whop.com/viralxvxpremium/?store=true"
CHAT_LINK = os.getenv("TELEGRAM_CHAT", "https://t.me/+PaqyU7Z-VQQ0ZTBh")
ADMIN_ID = os.getenv("ADMIN_ID")

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

# Menú principal solo para chat privado
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
        InlineKeyboardButton("🔄 Volver a empezar", callback_data="volver_empezar"),
    )
    return kb

# === BIENVENIDA SOLO EN CHAT PRIVADO ===
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    if message.chat.type != "private":
        return  # No hace nada en grupos
    user_id = message.from_user.id
    set_user_state(user_id, "inicio")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚀 Quiero Viralizar", callback_data="quiero_viralizar"))
    await message.answer(msj.BIENVENIDA, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "quiero_viralizar")
async def handle_quiero_viralizar(callback_query: types.CallbackQuery):
    if callback_query.message.chat.type != "private":
        return
    user_id = callback_query.from_user.id
    set_user_state(user_id, "esperando_email")
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, msj.PIDE_EMAIL, reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda message: get_user_state(message.from_user.id) == "esperando_email")
async def recibir_email(message: types.Message):
    if message.chat.type != "private":
        return
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
    if callback_query.message.chat.type != "private":
        return
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

# Bloquear mensajes fuera del flujo y fuera de privado
@dp.message_handler(lambda message: message.chat.type != "private")
async def bloquear_grupo(message: types.Message):
    # Borra el menú si aparece en grupo (handler de seguridad)
    await message.reply("Menú eliminado para todos.", reply_markup=ReplyKeyboardRemove())
    await message.delete()

@dp.message_handler(lambda message: get_user_state(message.from_user.id) not in ["esperando_email"])
async def bloquear_mensajes(message: types.Message):
    if message.chat.type != "private":
        return
    await message.delete()
    await bot.send_message(message.from_user.id, msj.AYUDA, reply_markup=None)

# MENÚ AVANZADO
@dp.callback_query_handler(lambda c: c.data == "faq")
async def menu_faq(callback_query: types.CallbackQuery):
    if callback_query.message.chat.type != "private":
        return
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, msj.FAQ, reply_markup=get_main_menu())

@dp.callback_query_handler(lambda c: c.data == "tutorial_discord")
async def menu_tutorial(callback_query: types.CallbackQuery):
    if callback_query.message.chat.type != "private":
        return
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, msj.TUTORIAL_DISCORD, reply_markup=get_main_menu())

@dp.callback_query_handler(lambda c: c.data == "soporte")
async def menu_soporte(callback_query: types.CallbackQuery):
    if callback_query.message.chat.type != "private":
        return
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, msj.SOPORTE, reply_markup=get_main_menu())
    if ADMIN_ID:
        await bot.send_message(int(ADMIN_ID), f"🛡️ Usuario {callback_query.from_user.id} ha solicitado soporte.")

@dp.callback_query_handler(lambda c: c.data == "volver_empezar")
async def volver_empezar(callback_query: types.CallbackQuery):
    if callback_query.message.chat.type != "private":
        return
    user_id = callback_query.from_user.id
    set_user_state(user_id, "inicio")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🚀 Quiero Viralizar", callback_data="quiero_viralizar"))
    await bot.send_message(user_id, "🔄 Has reiniciado el proceso.", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "perfil")
async def mi_perfil(callback_query: types.CallbackQuery):
    if callback_query.message.chat.type != "private":
        return
    user_id = callback_query.from_user.id
    email = get_user_email(user_id)
    estado = get_user_state(user_id)
    await bot.answer_callback_query(callback_query.id)
    texto = f"👤 *Tu perfil:*\n\nEstado actual: `{estado}`\nCorreo registrado: `{email or 'No registrado'}`"
    await bot.send_message(user_id, texto, reply_markup=get_main_menu(), parse_mode="Markdown")

# === LIMPIADOR TEMPORAL SOLO PARA ELIMINAR MENÚ DEL GRUPO ===
@dp.message_handler(commands=["limpiar_menu"])
async def limpiar_menu(message: types.Message):
    if message.chat.type == "private":
        await message.reply("Este comando solo es para grupos o canales.")
        return
    await message.answer("Menú eliminado para todos.", reply_markup=ReplyKeyboardRemove())

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
                # Expulsar
                try:
                    await bot.send_message(
                        user_id, 
                        "⚠️ No completaste tu registro y serás eliminado por inactividad.\nSi fue un error, vuelve a iniciar escribiendo /start."
                    )
                except Exception as e:
                    print(f"[WARN] No se pudo notificar a {user_id}: {e}")
                try:
                    await bot.kick_chat_member(chat_id=user_id, user_id=user_id)
                except Exception as e:
                    print(f"[WARN] No se pudo expulsar {user_id} (quizá no está en grupo): {e}")
                redis_client.delete(key)
                count_expulsados += 1
                print(f"[EXPULSADO] Usuario {user_id} eliminado por inactividad ({int(horas)}h).")
            elif email and horas > TIEMPO_RECORDATORIO_HRS:
                # Solo recordatorio
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("🔄 Reiniciar proceso", callback_data="volver_empezar"))
                try:
                    await bot.send_message(
                        user_id,
                        "👋 Aún no completaste tu acceso premium.\nPulsa abajo para reiniciar el proceso o pide ayuda en Soporte.",
                        reply_markup=kb
                    )
                    redis_client.hset(key, "last_update", now.isoformat())
                    count_recordados += 1
                    print(f"[RECORDATORIO] Usuario {user_id} recordado por inactividad ({int(horas)}h).")
                except Exception as e:
                    print(f"[WARN] No se pudo recordar {user_id}: {e}")
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
        await message.reply("\n".join(res[:50]))  # Hasta 50 por mensaje

if __name__ == "__main__":
    print("✅ Bot de Telegram VXbot FINAL listo y corriendo.")
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_limpieza())  # Arranca limpieza automática cada 24h
    executor.start_polling(dp, skip_updates=True)
