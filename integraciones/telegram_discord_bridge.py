# integraciones/telegram_discord_bridge.py

import os
import logging
import asyncio
import discord
from discord import File
from discord.ext import commands
from aiogram import Bot, Dispatcher, types
import aiohttp

# ===================== CONFIGURACIÓN =====================
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

# -------- MODO DE ENVÍO: 1=webhook, 2=directo, 3=fallback --------
# SOLO CAMBIA ESTE VALOR para cambiar comportamiento
MODO_ENVIO = int(os.getenv("MODO_ENVIO", "1"))  # Usa "1", "2" o "3"

DISCORD_TOKEN = get_env("DISCORD_TOKEN")
DISCORD_WEBHOOK_URL = get_env("DISCORD_WEBHOOK_URL", required=(MODO_ENVIO in [1, 3]))
DISCORD_CHANNEL_ID = get_env_int("DISCORD_CHANNEL_ID")  # Canal directo
DISCORD_CANAL_ID = get_env_int("DISCORD_CANAL_ID")  # Alias, para compatibilidad
TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CHANNEL_ID = get_env_int("TELEGRAM_CHANNEL_ID")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

# ===================== DISCORD BOT =====================
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
discord_bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== TELEGRAM BOT =====================
tg_bot = Bot(token=TELEGRAM_TOKEN)
tg_dp = Dispatcher(tg_bot)

# ===================== ENVÍO A DISCORD =====================
async def enviar_a_discord(msg, file_path=None, filename=None):
    """
    Modo 1: Solo Webhook
    Modo 2: Solo Canal Directo
    Modo 3: Webhook, si falla, Canal Directo (fallback)
    """
    logging.info(f"[enviar_a_discord] INICIO. MODO_ENVIO={MODO_ENVIO} | msg: {msg[:70]} | file: {filename}")
    # ----- MODO 1: SOLO WEBHOOK -----
    if MODO_ENVIO == 1:
        await enviar_via_webhook(msg, file_path, filename)
    # ----- MODO 2: SOLO CANAL DIRECTO -----
    elif MODO_ENVIO == 2:
        await enviar_via_canal(msg, file_path, filename)
    # ----- MODO 3: WEBHOOK + FALLBACK -----
    elif MODO_ENVIO == 3:
        try:
            await enviar_via_webhook(msg, file_path, filename)
        except Exception as e:
            logging.error(f"❌ Webhook falló, usando canal directo (fallback): {e}")
            await enviar_via_canal(msg, file_path, filename)
    else:
        logging.error(f"❌ MODO_ENVIO inválido: {MODO_ENVIO}")

async def enviar_via_webhook(msg, file_path=None, filename=None):
    if not DISCORD_WEBHOOK_URL:
        raise Exception("Webhook URL no configurado")
    async with aiohttp.ClientSession() as session:
        if file_path and filename:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("content", msg)
                form.add_field("file", f, filename=filename)
                async with session.post(DISCORD_WEBHOOK_URL, data=form) as resp:
                    if resp.status not in [200, 204]:
                        raise Exception(f"Webhook error {resp.status}")
                    logging.info(f"✅ [Tg→Discord] Archivo enviado via webhook")
        else:
            async with session.post(DISCORD_WEBHOOK_URL, json={"content": msg}) as resp:
                if resp.status not in [200, 204]:
                    raise Exception(f"Webhook error {resp.status}")
                logging.info(f"✅ [Tg→Discord] Texto enviado via webhook")

async def enviar_via_canal(msg, file_path=None, filename=None):
    canal_id = DISCORD_CHANNEL_ID or DISCORD_CANAL_ID
    canal = discord_bot.get_channel(canal_id)
    if not canal:
        raise Exception(f"No se encontró el canal Discord {canal_id}")
    if file_path and filename:
        await canal.send(msg, file=File(file_path, filename=filename))
        logging.info(f"✅ [Tg→Discord] Archivo enviado via canal directo")
    else:
        await canal.send(msg)
        logging.info(f"✅ [Tg→Discord] Texto enviado via canal directo")

# ===================== DISCORD → TELEGRAM =====================
@discord_bot.event
async def on_ready():
    logging.info(f"✅ Discord bot conectado como {discord_bot.user}")
    logging.info(f"🔗 Integrando canal Discord {DISCORD_CHANNEL_ID} ↔️ Telegram {TELEGRAM_CHANNEL_ID}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id not in [DISCORD_CHANNEL_ID, DISCORD_CANAL_ID]:
        return
    logging.info(f"[Discord→Tg] Recibido mensaje: {message.content[:100]}")
    try:
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
                    if resp.status == 200:
                        logging.info(f"✅ [Discord→Tg] Texto enviado: {message.content[:50]}...")
                    else:
                        error_text = await resp.text()
                        logging.error(f"❌ [Discord→Tg] Error {resp.status}: {error_text}")
        # Archivos adjuntos
        for attachment in message.attachments:
            try:
                async with aiohttp.ClientSession() as session:
                    file_bytes = await attachment.read()
                    data = aiohttp.FormData()
                    data.add_field("chat_id", str(TELEGRAM_CHANNEL_ID))
                    # Tipo de archivo
                    if attachment.content_type and "image" in attachment.content_type:
                        data.add_field("photo", file_bytes, filename=attachment.filename)
                        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
                    else:
                        data.add_field("document", file_bytes, filename=attachment.filename)
                        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
                    # Caption con info del usuario
                    if message.content:
                        data.add_field("caption", f"[Discord] {message.author.display_name}: {message.content}")
                    async with session.post(url, data=data) as resp:
                        if resp.status == 200:
                            logging.info(f"✅ [Discord→Tg] Archivo enviado: {attachment.filename}")
                        else:
                            error_text = await resp.text()
                            logging.error(f"❌ [Discord→Tg] Error archivo {resp.status}: {error_text}")
            except Exception as e:
                logging.error(f"❌ Error procesando archivo {attachment.filename}: {e}")
    except Exception as e:
        logging.error(f"❌ Error en on_message: {e}")

# ===================== TELEGRAM → DISCORD =====================
@tg_dp.channel_post_handler()
async def debug_all_channel_posts(message: types.Message):
    # Log ultra detallado
    logging.info(f"🐛 DEBUG - Canal post detectado:")
    logging.info(f"    RAW: {message}")
    logging.info(f"    Chat ID: {getattr(message.chat, 'id', None)}")
    logging.info(f"    Chat title: {getattr(message.chat, 'title', None)}")
    logging.info(f"    Text: {getattr(message, 'text', None)}")
    logging.info(f"    Caption: {getattr(message, 'caption', None)}")
    logging.info(f"    Photo: {getattr(message, 'photo', None)}")
    logging.info(f"    Document: {getattr(message, 'document', None)}")
    logging.info(f"    TELEGRAM_CHANNEL_ID configurado: {TELEGRAM_CHANNEL_ID}")
    if message.chat.id == TELEGRAM_CHANNEL_ID:
        logging.info("✅ IDs coinciden - procesando mensaje canal principal...")
    else:
        logging.warning(f"⚠️ IDs diferentes. Esperado: {TELEGRAM_CHANNEL_ID}, Recibido: {message.chat.id}")

@tg_dp.channel_post_handler(chat_id=TELEGRAM_CHANNEL_ID)
async def telegram_to_discord(message: types.Message):
    try:
        logging.info(f"🎯 Handler canal ACTIVADO - Chat: {message.chat.id}")
        # Procesar texto
        if message.text and not message.text.startswith('[Discord]'):
            logging.info(f"[Tg→Discord] Handler ENTRÓ al try.")
            logging.info(f">> Antes de enviar_a_discord (texto)")
            msg = f"[Telegram] {message.text}"
            await enviar_a_discord(msg)
            logging.info(f"✅ [Tg→Discord] Texto enviado exitosamente: {message.text}")
        elif message.text and message.text.startswith('[Discord]'):
            logging.info(f"⏭️ Mensaje ignorado (proviene de Discord)")
        # Procesar fotos
        if message.photo:
            photo = message.photo[-1]
            file = await photo.download()
            caption = message.caption or "Imagen desde Telegram"
            msg = f"[Telegram] {caption}"
            await enviar_a_discord(msg, file_path=file.name, filename=f"telegram_image_{photo.file_id}.jpg")
            logging.info(f"✅ [Tg→Discord] Imagen enviada")
            try:
                os.remove(file.name)
            except:
                pass
        # Procesar documentos
        if message.document:
            file = await message.document.download()
            caption = message.caption or "Archivo desde Telegram"
            msg = f"[Telegram] {caption}"
            await enviar_a_discord(msg, file_path=file.name, filename=message.document.file_name)
            logging.info(f"✅ [Tg→Discord] Documento enviado")
            try:
                os.remove(file.name)
            except:
                pass
    except Exception as e:
        logging.error(f"❌ Error general en telegram_to_discord: {e}")

# ===================== MAIN =====================
async def main():
    logging.info("🚀 Iniciando integración Discord ↔️ Telegram...")
    try:
        # Verificación de configuración
        chat = await tg_bot.get_chat(TELEGRAM_CHANNEL_ID)
        logging.info(f"✅ Canal Telegram encontrado: {chat.title} ({chat.id})")
        try:
            member = await tg_bot.get_chat_member(TELEGRAM_CHANNEL_ID, tg_bot.id)
            logging.info(f"🤖 Bot status en canal: {member.status}")
            if member.status not in ['administrator', 'creator']:
                logging.warning("⚠️ ADVERTENCIA: El bot NO es administrador del canal")
        except Exception as e:
            logging.warning(f"⚠️ No se pudo verificar permisos del bot: {e}")
        logging.info(f"🔧 Configuración:")
        logging.info(f"    Telegram Canal ID: {TELEGRAM_CHANNEL_ID}")
        logging.info(f"    Discord Canal ID: {DISCORD_CHANNEL_ID}")
        logging.info(f"    Webhook configurado: {'Sí' if DISCORD_WEBHOOK_URL else 'No'}")
    except Exception as e:
        logging.error(f"❌ Error verificando configuración: {e}")

    logging.info("📡 Iniciando polling de Telegram...")
    tg_task = asyncio.create_task(tg_dp.start_polling())
    logging.info("🎮 Conectando bot de Discord...")
    dc_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
    await asyncio.gather(tg_task, dc_task)

if __name__ == "__main__":
    try:
        required_vars = [
            "DISCORD_TOKEN", "TELEGRAM_TOKEN_INTEGRACION", "TELEGRAM_CHANNEL_ID"
        ]
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        if missing_vars:
            logging.error(f"❌ FALTAN VARIABLES DE ENTORNO: {', '.join(missing_vars)}")
            logging.error("💡 Asegúrate de tener un archivo .env o variables de sistema configuradas")
            exit(1)
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Bot detenido por el usuario")
    except Exception as e:
        logging.error(f"💥 Error crítico: {e}")
        import traceback
        logging.error(traceback.format_exc())
        exit(1)
