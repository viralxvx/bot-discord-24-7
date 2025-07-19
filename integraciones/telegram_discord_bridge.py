import os
import logging
import aiohttp
import discord
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

# === Variables de entorno ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_ID = int(os.getenv("DISCORD_CANAL_TELEGRAM"))  # canal Discord para reflejar (ej: 1395768275769757806)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Si usas webhook para enviar archivos, etc

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_INTEGRACION")  # SOLO para integración, diferente al bot principal
TELEGRAM_GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID"))   # Ejemplo: -1002692314719 (grupo/canal público)

if not DISCORD_TOKEN or not TELEGRAM_TOKEN or not DISCORD_CANAL_ID or not TELEGRAM_GROUP_ID:
    raise Exception("❌ Faltan variables de entorno críticas (DISCORD_TOKEN, TELEGRAM_TOKEN_INTEGRACION, DISCORD_CANAL_TELEGRAM, TELEGRAM_GROUP_ID)")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

# === Discord Client ===
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
discord_bot = discord.Client(intents=intents)

# === Telegram Bot ===
tg_bot = Bot(token=TELEGRAM_TOKEN)
tg_dp = Dispatcher(tg_bot)

# ======= DISCORD → TELEGRAM =======
@discord_bot.event
async def on_ready():
    logging.info(f"✅ Discord ↔️ Telegram integración activa como {discord_bot.user}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != DISCORD_CANAL_ID:
        return
    text = f"[Discord] {message.author.display_name}: {message.content}"
    logging.info(f"🟣 [Discord→Tg] Mensaje en canal Discord {message.channel.id}: {message.id}")

    # Archivos
    files = []
    if message.attachments:
        for attachment in message.attachments:
            files.append(attachment.url)

    # Enviar texto a Telegram
    if message.content.strip():
        try:
            await tg_bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=text)
            logging.info("➡️ [Discord→Tg] Texto enviado.")
        except Exception as e:
            logging.error(f"❌ [Discord→Tg] Error enviando texto: {e}")

    # Enviar archivos a Telegram
    for url in files:
        try:
            await tg_bot.send_document(chat_id=TELEGRAM_GROUP_ID, document=url)
            logging.info(f"➡️ [Discord→Tg] Archivo enviado: {url}")
        except Exception as e:
            logging.error(f"❌ [Discord→Tg] Error enviando archivo: {e}")

# ======= TELEGRAM → DISCORD =======
@tg_dp.message_handler(lambda msg: msg.chat.id == TELEGRAM_GROUP_ID)
async def handle_telegram_message(message: types.Message):
    # Texto
    if message.text:
        content = f"[Telegram] {message.from_user.first_name}: {message.text}"
        logging.info(f"🟢 [Tg→Discord] Texto recibido: {content}")

        # Si tienes un webhook para archivos/embeds:
        if DISCORD_WEBHOOK_URL:
            data = {"content": content}
            async with aiohttp.ClientSession() as session:
                async with session.post(DISCORD_WEBHOOK_URL, json=data) as resp:
                    if resp.status == 204 or resp.status == 200:
                        logging.info(f"➡️ [Tg→Discord] Texto enviado por webhook.")
                    else:
                        logging.warning(f"❌ [Tg→Discord] Error webhook: {await resp.text()}")
        else:
            # Envía como mensaje normal
            channel = discord_bot.get_channel(DISCORD_CANAL_ID)
            if channel:
                await channel.send(content)
                logging.info(f"➡️ [Tg→Discord] Texto enviado a canal Discord.")

    # Archivos/documentos/imágenes
    elif message.document or message.photo:
        # Usa el archivo más grande (última foto suele ser la mejor calidad)
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name
        else:
            file_id = message.photo[-1].file_id
            file_name = "foto_telegram.jpg"
        file = await tg_bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"

        # Webhook soporta files si es multipart/form-data, aquí lo simplificamos como enlace
        content = f"[Telegram] {message.from_user.first_name} envió un archivo: {file_name or 'archivo'}\n{file_url}"
        logging.info(f"🟢 [Tg→Discord] Archivo recibido: {file_url}")

        # Envía por webhook
        if DISCORD_WEBHOOK_URL:
            data = {"content": content}
            async with aiohttp.ClientSession() as session:
                async with session.post(DISCORD_WEBHOOK_URL, json=data) as resp:
                    if resp.status == 204 or resp.status == 200:
                        logging.info(f"➡️ [Tg→Discord] Archivo enviado por webhook.")
                    else:
                        logging.warning(f"❌ [Tg→Discord] Error webhook archivo: {await resp.text()}")
        else:
            channel = discord_bot.get_channel(DISCORD_CANAL_ID)
            if channel:
                await channel.send(content)
                logging.info(f"➡️ [Tg→Discord] Archivo enviado a canal Discord.")

# ========== EJECUCIÓN ==========
async def main():
    discord_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
    tg_polling_task = asyncio.create_task(tg_dp.start_polling())
    await asyncio.gather(discord_task, tg_polling_task)

if __name__ == "__main__":
    logging.info("🔗 Integración Discord ↔️ Telegram corriendo...")
    logging.info("▶️ Polling canal Telegram → Discord...")
    asyncio.run(main())
