# integraciones/telegram_discord_bridge.py

import os
import logging
import asyncio

import discord
from discord import File
from discord.ext import commands
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile

import aiohttp

# ========== CONFIG & VALIDACIÓN DE VARIABLES ==========

def get_env(name, required=True):
    value = os.getenv(name)
    if required and (value is None or value.strip() == ""):
        raise Exception(f"❌ FALTA VARIABLE DE ENTORNO: {name}")
    return value.strip() if value else value

def get_env_int(name):
    v = get_env(name)
    try:
        return int(v)
    except:
        raise Exception(f"❌ VARIABLE DE ENTORNO {name} debe ser un número entero. Valor actual: {v}")

DISCORD_TOKEN = get_env("DISCORD_TOKEN")
DISCORD_CANAL_ID = get_env_int("DISCORD_CANAL_TELEGRAM")
DISCORD_WEBHOOK_URL = get_env("DISCORD_WEBHOOK_URL", required=False)  # Puede ser "" si no quieres usar webhook
TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CHANNEL_ID = get_env_int("TELEGRAM_CHANNEL_ID")  # canal @viralxvx (Comunidad | VX)

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

# ========== DISCORD ==========
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

discord_bot = commands.Bot(command_prefix="!", intents=intents)

# ========== TELEGRAM ==========
tg_bot = Bot(token=TELEGRAM_TOKEN)
tg_dp = Dispatcher(tg_bot)

# ========== UTILITY: ENVIAR A DISCORD ==========
async def enviar_a_discord(msg, file_path=None, filename=None):
    # Prioridad: webhook > canal directo
    if DISCORD_WEBHOOK_URL:
        async with aiohttp.ClientSession() as session:
            data = {"content": msg}
            files = None
            if file_path and filename:
                with open(file_path, "rb") as f:
                    form = aiohttp.FormData()
                    form.add_field("content", msg)
                    form.add_field("file", f, filename=filename)
                    files = form
                    await session.post(DISCORD_WEBHOOK_URL, data=form)
                    logging.info(f"➡️ [Tg→Discord] Archivo status via webhook")
            else:
                await session.post(DISCORD_WEBHOOK_URL, json=data)
                logging.info(f"➡️ [Tg→Discord] Texto status via webhook")
    else:
        canal = discord_bot.get_channel(DISCORD_CANAL_ID)
        if canal:
            if file_path and filename:
                await canal.send(msg, file=File(file_path, filename=filename))
                logging.info(f"➡️ [Tg→Discord] Archivo status canal")
            else:
                await canal.send(msg)
                logging.info(f"➡️ [Tg→Discord] Texto status canal")

# ========== DISCORD → TELEGRAM ==========
@discord_bot.event
async def on_ready():
    logging.info(f"✅ Discord ↔️ Telegram integración activa como {discord_bot.user}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != DISCORD_CANAL_ID:
        return

    # Texto
    if message.content.strip():
        text = f"[Discord] {message.author.display_name}: {message.content}"
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHANNEL_ID,
                "text": text
            }
            async with session.post(url, data=payload) as resp:
                status = await resp.text()
                logging.info(f"➡️ [Discord→Tg] Texto status: {resp.status}, resp: {status}")

    # Imágenes/archivos adjuntos
    for attachment in message.attachments:
        async with aiohttp.ClientSession() as session:
            file_bytes = await attachment.read()
            data = aiohttp.FormData()
            data.add_field("chat_id", str(TELEGRAM_CHANNEL_ID))
            if attachment.content_type and "image" in attachment.content_type:
                data.add_field("photo", file_bytes, filename=attachment.filename)
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            else:
                data.add_field("document", file_bytes, filename=attachment.filename)
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
            async with session.post(url, data=data) as resp:
                logging.info(f"➡️ [Discord→Tg] Archivo status: {resp.status} ({attachment.filename})")

# ========== TELEGRAM CANAL (NO GRUPO) → DISCORD ==========
@tg_dp.channel_post_handler(chat_id=TELEGRAM_CHANNEL_ID)
async def telegram_to_discord(message: types.Message):
    # No reenvíes mensajes que ya vienen de Discord
    if message.text and not message.text.startswith('[Discord]'):
        try:
            msg = f"[Telegram] {message.text}"
            await enviar_a_discord(msg)
            logging.info(f"✅ [Tg→Discord] Texto enviado: {message.text}")
        except Exception as e:
            logging.error(f"❌ Error enviando texto a Discord: {e}")

    # Fotos
    if message.photo:
        try:
            file = await message.photo[-1].download()
            caption = message.caption or ""
            msg = f"[Telegram] {caption}"
            await enviar_a_discord(msg, file_path=file.name, filename=file.name)
            logging.info(f"✅ [Tg→Discord] Imagen enviada")
        except Exception as e:
            logging.error(f"❌ Error enviando imagen a Discord: {e}")

    # Documentos
    if message.document:
        try:
            file = await message.document.download()
            caption = message.caption or ""
            msg = f"[Telegram] {caption}"
            await enviar_a_discord(msg, file_path=file.name, filename=file.name)
            logging.info(f"✅ [Tg→Discord] Archivo enviado")
        except Exception as e:
            logging.error(f"❌ Error enviando archivo a Discord: {e}")

# ========== COMANDO EXTRA: /getid (SOLO PARA USO ADMIN) ==========
@tg_dp.message_handler(commands=["getid"])
async def cmd_getid(message: types.Message):
    try:
        chat = message.chat
        msg = f"[TG] /getid en chat '{chat.title}' (type: {chat.type}) id: {chat.id}"
        await message.reply(msg)
        logging.info(msg)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# ========== MAIN (EJECUCIÓN CONCURRENTE) ==========
async def main():
    logging.info("🔗 Integración Discord ↔️ Telegram corriendo...")
    tg_task = asyncio.create_task(tg_dp.start_polling())
    dc_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
    await asyncio.gather(tg_task, dc_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Error fatal: {e}")
