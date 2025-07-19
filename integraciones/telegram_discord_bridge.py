import os
import logging
import aiohttp
import discord
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils.executor import start_polling
from dotenv import load_dotenv
import asyncio

load_dotenv()

# --- Variables de entorno ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_ID = int(os.getenv("DISCORD_CANAL_TELEGRAM"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_GRUPO_ID = int(os.getenv("TELEGRAM_GRUPO_ID"))

if not all([DISCORD_TOKEN, DISCORD_CANAL_ID, TELEGRAM_TOKEN, TELEGRAM_GRUPO_ID]):
    raise Exception("❌ Faltan variables de entorno: revisa los tokens y IDs.")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)

# --- Telegram ---
tg_bot = Bot(token=TELEGRAM_TOKEN)
tg_dp = Dispatcher(tg_bot)

# --- Discord ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_bot = discord.Client(intents=intents)

# --- TELEGRAM → DISCORD ---
@tg_dp.message_handler(content_types=types.ContentTypes.ANY)
async def tg_to_discord(message: types.Message):
    if message.chat.id != TELEGRAM_GRUPO_ID:
        logging.warning(f"[Tg→Discord] Ignorado: {message.chat.type} ({message.chat.id})")
        return

    try:
        text = (message.text or message.caption or "").strip()
        files = []

        # Adjuntos: fotos, docs, video, audio
        if message.photo:
            photo = message.photo[-1]
            file = await tg_bot.get_file(photo.file_id)
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"
            files.append(("photo", file_url))
        elif message.document:
            file = await tg_bot.get_file(message.document.file_id)
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"
            files.append(("document", file_url))
        elif message.video:
            file = await tg_bot.get_file(message.video.file_id)
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"
            files.append(("video", file_url))
        elif message.audio:
            file = await tg_bot.get_file(message.audio.file_id)
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"
            files.append(("audio", file_url))

        username = message.from_user.full_name if message.from_user else "Desconocido"
        final_text = f"[Telegram] {username}: {text or '[Archivo adjunto]'}"
        discord_channel = discord_bot.get_channel(DISCORD_CANAL_ID)
        if not discord_channel:
            logging.error(f"[Tg→Discord] No se pudo acceder al canal Discord {DISCORD_CANAL_ID}")
            return

        if text:
            await discord_channel.send(final_text)

        for tipo, url in files:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        filename = url.split("/")[-1]
                        discord_file = discord.File(fp=bytearray(data), filename=filename)
                        await discord_channel.send(file=discord_file)
                        logging.info(f"[Tg→Discord] Archivo ({tipo}) enviado: {filename}")
                    else:
                        logging.error(f"[Tg→Discord] Fallo descarga archivo ({tipo}): {url}")

        logging.info(f"[Tg→Discord] Replicado: {final_text}")

    except Exception as e:
        logging.error(f"[Tg→Discord] Error replicando: {e}")

# --- DISCORD → TELEGRAM ---
@discord_bot.event
async def on_ready():
    logging.info(f"✅ Discord ↔️ Telegram integración activa como {discord_bot.user}")

@discord_bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != DISCORD_CANAL_ID:
        return

    try:
        text = message.content or ""
        author = message.author.display_name
        final_text = f"[Discord] {author}: {text or '[Archivo adjunto]'}"
        files = message.attachments

        if text:
            await tg_bot.send_message(TELEGRAM_GRUPO_ID, final_text)

        for adj in files:
            file_bytes = await adj.read()
            filename = adj.filename
            if adj.content_type and adj.content_type.startswith("image"):
                await tg_bot.send_photo(TELEGRAM_GRUPO_ID, file_bytes, caption=final_text if not text else None)
            elif adj.content_type and adj.content_type.startswith("video"):
                await tg_bot.send_video(TELEGRAM_GRUPO_ID, file_bytes, caption=final_text if not text else None)
            else:
                await tg_bot.send_document(TELEGRAM_GRUPO_ID, file_bytes, caption=final_text if not text else None)
            logging.info(f"[Discord→Tg] Archivo enviado: {filename}")

        logging.info(f"[Discord→Tg] Replicado: {final_text}")

    except Exception as e:
        logging.error(f"[Discord→Tg] Error replicando: {e}")

# --- ARRANQUE FINAL DE AMBOS BOTS, SIN BLOQUEAR EL EVENT LOOP ---
async def main():
    discord_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
    tg_polling_task = asyncio.create_task(tg_dp.start_polling(skip_updates=True))
    await asyncio.gather(discord_task, tg_polling_task)

if __name__ == "__main__":
    logging.info("🔗 Integración Discord ↔️ Telegram corriendo...")
    logging.info("▶️ Polling canal Telegram → Discord...")
    asyncio.run(main())
