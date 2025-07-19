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
DISCORD_WEBHOOK_URL = get_env("DISCORD_WEBHOOK_URL", required=False)
TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CHANNEL_ID = get_env_int("TELEGRAM_CHANNEL_ID")

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
    logging.info(f"⏳ [Tg→Discord] Iniciando envío: {msg[:80]}... Archivo: {filename if filename else 'N/A'}")
    try:
        if DISCORD_WEBHOOK_URL:
            logging.info(f"[Tg→Discord] Usando WEBHOOK: {DISCORD_WEBHOOK_URL}")
            async with aiohttp.ClientSession() as session:
                if file_path and filename:
                    with open(file_path, "rb") as f:
                        form = aiohttp.FormData()
                        form.add_field("content", msg)
                        form.add_field("file", f, filename=filename)
                        async with session.post(DISCORD_WEBHOOK_URL, data=form) as resp:
                            text = await resp.text()
                            logging.info(f"✅ [Tg→Discord] Archivo enviado via webhook. Status: {resp.status} Resp: {text[:100]}")
                            if resp.status != 200:
                                raise Exception(f"Webhook falló: {resp.status}")
                else:
                    async with session.post(DISCORD_WEBHOOK_URL, json={"content": msg}) as resp:
                        text = await resp.text()
                        logging.info(f"✅ [Tg→Discord] Texto enviado via webhook. Status: {resp.status} Resp: {text[:100]}")
                        if resp.status != 200:
                            raise Exception(f"Webhook falló: {resp.status}")
        else:
            logging.info(f"[Tg→Discord] Usando envío directo a canal ID {DISCORD_CANAL_ID}")
            canal = discord_bot.get_channel(DISCORD_CANAL_ID)
            if canal:
                if file_path and filename:
                    await canal.send(msg, file=File(file_path, filename=filename))
                    logging.info(f"✅ [Tg→Discord] Archivo enviado via canal")
                else:
                    await canal.send(msg)
                    logging.info(f"✅ [Tg→Discord] Texto enviado via canal")
            else:
                logging.error(f"❌ No se encontró el canal Discord {DISCORD_CANAL_ID}")
                raise Exception("Canal Discord no encontrado")
    except Exception as e:
        logging.error(f"❌ Error en enviar_a_discord: {e}")
        import traceback
        logging.error(traceback.format_exc())
        # Fallback directo si existe canal y falló el webhook
        try:
            canal = discord_bot.get_channel(DISCORD_CANAL_ID)
            if canal:
                if file_path and filename:
                    await canal.send(msg, file=File(file_path, filename=filename))
                    logging.info(f"✅ [Tg→Discord] Archivo enviado via canal (fallback)")
                else:
                    await canal.send(msg)
                    logging.info(f"✅ [Tg→Discord] Texto enviado via canal (fallback)")
        except Exception as fallback_error:
            logging.error(f"❌ Fallback total falló: {fallback_error}")
            logging.error(traceback.format_exc())

# ========== DISCORD → TELEGRAM ==========
@discord_bot.event
async def on_ready():
    logging.info(f"✅ Discord bot conectado como {discord_bot.user}")
    logging.info(f"🔗 Integrando canal Discord {DISCORD_CANAL_ID} ↔️ Telegram {TELEGRAM_CHANNEL_ID}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != DISCORD_CANAL_ID:
        return
    try:
        logging.info(f"[Discord→Tg] Recibido mensaje: {message.content}")
        # Enviar texto
        if message.content.strip():
            text = f"[Discord] {message.author.display_name}: {message.content}"
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                payload = {
                    "chat_id": TELEGRAM_CHANNEL_ID,
                    "text": text
                }
                async with session.post(url, data=payload) as resp:
                    resp_txt = await resp.text()
                    if resp.status == 200:
                        logging.info(f"✅ [Discord→Tg] Texto enviado: {message.content[:50]}...")
                    else:
                        logging.error(f"❌ [Discord→Tg] Error {resp.status}: {resp_txt}")
        # Enviar archivos adjuntos
        for attachment in message.attachments:
            try:
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
                    if message.content:
                        data.add_field("caption", f"[Discord] {message.author.display_name}: {message.content}")
                    async with session.post(url, data=data) as resp:
                        resp_txt = await resp.text()
                        if resp.status == 200:
                            logging.info(f"✅ [Discord→Tg] Archivo enviado: {attachment.filename}")
                        else:
                            logging.error(f"❌ [Discord→Tg] Error archivo {resp.status}: {resp_txt}")
            except Exception as e:
                logging.error(f"❌ Error procesando archivo {attachment.filename}: {e}")
    except Exception as e:
        logging.error(f"❌ Error en on_message: {e}")

# ========== TELEGRAM → DISCORD ==========
@tg_dp.channel_post_handler()
async def debug_all_channel_posts(message: types.Message):
    logging.info(f"🐛 DEBUG - Canal post detectado:")
    logging.info(f"   Chat ID: {message.chat.id}")
    logging.info(f"   Chat title: {getattr(message.chat, 'title', '-')}")
    logging.info(f"   Text: {message.text}")
    logging.info(f"   TELEGRAM_CHANNEL_ID configurado: {TELEGRAM_CHANNEL_ID}")
    if message.chat.id == TELEGRAM_CHANNEL_ID:
        logging.info("✅ IDs coinciden - procesando mensaje...")
    else:
        logging.warning(f"⚠️ IDs diferentes. Esperado: {TELEGRAM_CHANNEL_ID}, Recibido: {message.chat.id}")

@tg_dp.channel_post_handler(chat_id=TELEGRAM_CHANNEL_ID)
async def telegram_to_discord(message: types.Message):
    try:
        logging.info(f"🎯 Handler específico activado - Chat: {message.chat.id}")
        # Procesar texto (evitar loops)
        if message.text and not message.text.startswith('[Discord]'):
            try:
                msg = f"[Telegram] {message.text}"
                logging.info(f"📤 Enviando texto a Discord: {msg[:100]}...")
                await enviar_a_discord(msg)
                logging.info(f"✅ [Tg→Discord] Texto enviado exitosamente")
            except Exception as e:
                logging.error(f"❌ Error enviando texto: {e}")
        elif message.text and message.text.startswith('[Discord]'):
            logging.info(f"⏭️ Mensaje ignorado (proviene de Discord)")
        else:
            logging.info("⏭️ Mensaje sin texto, ignorado")

        # Fotos
        if message.photo:
            try:
                photo = message.photo[-1]  # Mejor calidad
                file = await photo.download()
                caption = message.caption or "Imagen desde Telegram"
                msg = f"[Telegram] {caption}"
                logging.info(f"📤 Enviando imagen a Discord...")
                await enviar_a_discord(msg, file_path=file.name, filename=f"telegram_image_{photo.file_id}.jpg")
                logging.info(f"✅ [Tg→Discord] Imagen enviada")
                try:
                    os.remove(file.name)
                except:
                    pass
            except Exception as e:
                logging.error(f"❌ Error enviando imagen: {e}")

        # Documentos
        if message.document:
            try:
                file = await message.document.download()
                caption = message.caption or "Archivo desde Telegram"
                msg = f"[Telegram] {caption}"
                logging.info(f"📤 Enviando documento a Discord: {message.document.file_name}")
                await enviar_a_discord(msg, file_path=file.name, filename=message.document.file_name)
                logging.info(f"✅ [Tg→Discord] Documento enviado")
                try:
                    os.remove(file.name)
                except:
                    pass
            except Exception as e:
                logging.error(f"❌ Error enviando documento: {e}")

    except Exception as e:
        logging.error(f"❌ Error general en telegram_to_discord: {e}")
        import traceback
        logging.error(traceback.format_exc())

# ========== COMANDO DE TEST Y DIAGNÓSTICO ==========
@tg_dp.message_handler(commands=["testdiscord"])
async def cmd_testdiscord(message: types.Message):
    try:
        test_msg = f"⚡️ [TEST] Mensaje de test desde Telegram a Discord. User: {message.from_user.id}"
        logging.info(f"[CMD] /testdiscord disparado: {test_msg}")
        await enviar_a_discord(test_msg)
        await message.reply("✅ Test enviado a Discord.")
    except Exception as e:
        logging.error(f"[CMD] /testdiscord error: {e}")
        await message.reply(f"❌ Error enviando test: {e}")

# ========== MAIN ==========
async def main():
    logging.info("🚀 Iniciando integración Discord ↔️ Telegram...")
    tg_task = asyncio.create_task(tg_dp.start_polling())
    dc_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
    await asyncio.gather(tg_task, dc_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Bot detenido por el usuario")
    except Exception as e:
        logging.error(f"💥 Error crítico: {e}")
        import traceback
        logging.error(traceback.format_exc())
        exit(1)
