import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import aiohttp
import discord
import logging

# === LOGGING DETALLADO ===
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

# === VARIABLES DE ENTORNO ===
TELEGRAM_TOKEN_INTEGRACION = os.getenv("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # username sin @
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_TELEGRAM = int(os.getenv("DISCORD_CANAL_TELEGRAM"))

if not (TELEGRAM_TOKEN_INTEGRACION and TELEGRAM_CANAL and DISCORD_WEBHOOK_URL and DISCORD_TOKEN and DISCORD_CANAL_TELEGRAM):
    raise Exception("❌ Faltan variables de entorno para integración completa")

# === TELEGRAM BOT CONFIGURACIÓN ===
tg_bot = Bot(token=TELEGRAM_TOKEN_INTEGRACION)
tg_dp = Dispatcher(tg_bot)

async def enviar_a_discord(text=None, files=None):
    async with aiohttp.ClientSession() as session:
        data = {}
        files_data = []
        if text:
            data['content'] = text

        if files:
            for i, (filename, content, mime) in enumerate(files):
                files_data.append(('file'+str(i+1), (filename, content, mime)))

        if files_data:
            form = aiohttp.FormData()
            for k, v in data.items():
                form.add_field(k, v)
            for f in files_data:
                form.add_field(f[0], f[1][1], filename=f[1][0], content_type=f[1][2])
            async with session.post(DISCORD_WEBHOOK_URL, data=form) as resp:
                logging.info(f"➡️ [Tg→Discord] Enviando archivos... status: {resp.status}")
                if resp.status not in [200,204]:
                    logging.error(f"❌ [Tg→Discord] Error archivos: {await resp.text()}")
        else:
            async with session.post(DISCORD_WEBHOOK_URL, json=data) as resp:
                logging.info(f"➡️ [Tg→Discord] Enviando texto... status: {resp.status}")
                if resp.status not in [200,204]:
                    logging.error(f"❌ [Tg→Discord] Error texto: {await resp.text()}")

@tg_dp.message_handler()
async def handle_telegram_msg(message: types.Message):
    if message.chat.type == "channel" and message.chat.username and message.chat.username.lower() == TELEGRAM_CANAL.lower():
        logging.info(f"🟢 [Tg→Discord] Mensaje recibido en canal {TELEGRAM_CANAL}: {message.message_id}")

        # Soporte: Texto
        text = f"**[Telegram]**\n{message.text or ''}"

        # Soporte: Multimedia
        files = []
        # Fotos
        if message.photo:
            file_id = message.photo[-1].file_id
            file = await tg_bot.get_file(file_id)
            f = await tg_bot.download_file(file.file_path)
            files.append((f"photo_{file_id}.jpg", f, 'image/jpeg'))
        # Documentos
        if message.document:
            file_id = message.document.file_id
            file = await tg_bot.get_file(file_id)
            f = await tg_bot.download_file(file.file_path)
            files.append((message.document.file_name or f"doc_{file_id}", f, message.document.mime_type or 'application/octet-stream'))
        # Stickers
        if message.sticker:
            file_id = message.sticker.file_id
            file = await tg_bot.get_file(file_id)
            f = await tg_bot.download_file(file.file_path)
            files.append((f"sticker_{file_id}.webp", f, 'image/webp'))
        # Video
        if message.video:
            file_id = message.video.file_id
            file = await tg_bot.get_file(file_id)
            f = await tg_bot.download_file(file.file_path)
            files.append((message.video.file_name or f"video_{file_id}.mp4", f, 'video/mp4'))
        # Audio/Voice
        if message.voice:
            file_id = message.voice.file_id
            file = await tg_bot.get_file(file_id)
            f = await tg_bot.download_file(file.file_path)
            files.append((f"voice_{file_id}.ogg", f, 'audio/ogg'))
        if message.audio:
            file_id = message.audio.file_id
            file = await tg_bot.get_file(file_id)
            f = await tg_bot.download_file(file.file_path)
            files.append((message.audio.file_name or f"audio_{file_id}.mp3", f, 'audio/mpeg'))

        if files:
            await enviar_a_discord(text, files)
        elif text.strip():
            await enviar_a_discord(text)
        else:
            logging.warning("[Tg→Discord] Mensaje sin contenido, ignorado.")
    else:
        logging.warning(f"[Tg→Discord] Ignorado: {message.chat.type} ({message.chat.id})")

async def telegram_polling():
    logging.info("▶️ Polling canal Telegram → Discord...")
    await tg_dp.start_polling()

# === DISCORD BOT CONFIGURACIÓN ===
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_bot = discord.Client(intents=intents)

@discord_bot.event
async def on_ready():
    logging.info(f"✅ Discord ↔ Telegram integración activa como {discord_bot.user}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != DISCORD_CANAL_TELEGRAM:
        return

    logging.info(f"🟣 [Discord→Tg] Mensaje en canal Discord {DISCORD_CANAL_TELEGRAM}: {message.id}")

    # Mensaje de texto
    text = f"[Discord] {message.author.display_name}: {message.content}"

    # Adjuntos (imágenes, docs, etc)
    files = []
    for a in message.attachments:
        content = await a.read()
        files.append((a.filename, content, a.content_type or 'application/octet-stream'))

    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN_INTEGRACION}/sendMessage"
        if files:
            # Enviar cada archivo como mensaje separado (Telegram limita multi-archivos en bots)
            for filename, content, mime in files:
                file_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN_INTEGRACION}/sendDocument"
                form = aiohttp.FormData()
                form.add_field("chat_id", f"@{TELEGRAM_CANAL}")
                form.add_field("caption", text)
                form.add_field("document", content, filename=filename, content_type=mime)
                async with session.post(file_url, data=form) as resp:
                    logging.info(f"➡️ [Discord→Tg] Archivo enviado: {filename} status: {resp.status}")
                    if resp.status != 200:
                        logging.error(f"❌ [Discord→Tg] Error archivo: {await resp.text()}")
        else:
            payload = {"chat_id": f"@{TELEGRAM_CANAL}", "text": text}
            async with session.post(url, data=payload) as resp:
                logging.info(f"➡️ [Discord→Tg] Texto status: {resp.status}")
                if resp.status != 200:
                    logging.error(f"❌ [Discord→Tg] Error texto: {await resp.text()}")

async def main():
    await asyncio.gather(
        telegram_polling(),
        discord_bot.start(DISCORD_TOKEN)
    )

if __name__ == "__main__":
    logging.info("🔗 Integración Discord ↔ Telegram corriendo...")
    asyncio.run(main())
