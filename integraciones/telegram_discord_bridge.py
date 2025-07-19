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

DISCORD_TOKEN = get_env("DISCORD_TOKEN")
DISCORD_CANAL_ID = int(get_env("DISCORD_CANAL_TELEGRAM"))
DISCORD_WEBHOOK_URL = get_env("DISCORD_WEBHOOK_URL")  # Puede ser "" si no quieres usar webhook
TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CHANNEL_USERNAME = get_env("TELEGRAM_CHANNEL_USERNAME")  # Ej: viralxvx (sin @)

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
                "chat_id": f"@{TELEGRAM_CHANNEL_USERNAME}",
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
            data.add_field("chat_id", f"@{TELEGRAM_CHANNEL_USERNAME}")
            if attachment.content_type and "image" in attachment.content_type:
                data.add_field("photo", file_bytes, filename=attachment.filename)
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            else:
                data.add_field("document", file_bytes, filename=attachment.filename)
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
            async with session.post(url, data=data) as resp:
                logging.info(f"➡️ [Discord→Tg] Archivo status: {resp.status} ({attachment.filename})")

# ========== TELEGRAM → DISCORD ==========

@tg_dp.message_handler(lambda m: m.chat.username and m.chat.username.lower() == TELEGRAM_CHANNEL_USERNAME.lower())
async def tg_to_discord(message: types.Message):
    if message.from_user and message.from_user.is_bot:
        return
    try:
        # Mensajes de texto
        if message.text:
            msg = f"[Telegram] {message.from_user.full_name}: {message.text}"
            if DISCORD_WEBHOOK_URL:
                async with aiohttp.ClientSession() as session:
                    payload = {"content": msg}
                    async with session.post(DISCORD_WEBHOOK_URL, json=payload) as resp:
                        logging.info(f"➡️ [Tg→Discord] Texto status: {resp.status}")
            else:
                canal = discord_bot.get_channel(DISCORD_CANAL_ID)
                if canal:
                    await canal.send(msg)
                logging.info(f"➡️ [Tg→Discord] Texto canal")

        # Fotos
        elif message.photo:
            file = await message.photo[-1].download()
            file_name = file.name
            caption = message.caption or ""
            content = f"[Telegram] {message.from_user.full_name}: {caption}"
            if DISCORD_WEBHOOK_URL:
                with open(file_name, "rb") as f:
                    async with aiohttp.ClientSession() as session:
                        form = aiohttp.FormData()
                        form.add_field("content", content)
                        form.add_field("file", f, filename=file_name)
                        async with session.post(DISCORD_WEBHOOK_URL, data=form) as resp:
                            logging.info(f"➡️ [Tg→Discord] Imagen status: {resp.status}")
            else:
                canal = discord_bot.get_channel(DISCORD_CANAL_ID)
                if canal:
                    await canal.send(content, file=File(file_name))
                logging.info(f"➡️ [Tg→Discord] Imagen canal")

        # Documentos
        elif message.document:
            file = await message.document.download()
            file_name = file.name
            caption = message.caption or ""
            content = f"[Telegram] {message.from_user.full_name}: {caption}"
            if DISCORD_WEBHOOK_URL:
                with open(file_name, "rb") as f:
                    async with aiohttp.ClientSession() as session:
                        form = aiohttp.FormData()
                        form.add_field("content", content)
                        form.add_field("file", f, filename=file_name)
                        async with session.post(DISCORD_WEBHOOK_URL, data=form) as resp:
                            logging.info(f"➡️ [Tg→Discord] Archivo status: {resp.status}")
            else:
                canal = discord_bot.get_channel(DISCORD_CANAL_ID)
                if canal:
                    await canal.send(content, file=File(file_name))
                logging.info(f"➡️ [Tg→Discord] Archivo canal")

    except Exception as e:
        logging.error(f"[Tg→Discord] Error procesando mensaje: {e}")

# ========== COMANDO /getid ==========

@tg_dp.message_handler(commands=['getid'])
async def handle_getid(message: types.Message):
    chat = message.chat
    chat_type = chat.type
    chat_id = chat.id
    name = chat.title or chat.full_name or "(sin nombre)"
    await message.reply(f"[TG] /getid en chat '{name}' (type: {chat_type}) id: {chat_id}")

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
