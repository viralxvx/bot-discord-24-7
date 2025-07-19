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
    logging.info(f"[enviar_a_discord] INICIO. msg='{msg[:80]}', file_path={file_path}, filename={filename}")
    try:
        if DISCORD_WEBHOOK_URL:
            async with aiohttp.ClientSession() as session:
                if file_path and filename:
                    with open(file_path, "rb") as f:
                        form = aiohttp.FormData()
                        form.add_field("content", msg)
                        form.add_field("file", f, filename=filename)
                        async with session.post(DISCORD_WEBHOOK_URL, data=form) as resp:
                            logging.info(f"[enviar_a_discord] Webhook archivo status: {resp.status}")
                            if resp.status == 200:
                                logging.info(f"✅ [Tg→Discord] Archivo enviado via webhook")
                            else:
                                logging.error(f"❌ Webhook falló ({resp.status}), intentando canal...")
                                raise Exception("Webhook failed")
                else:
                    async with session.post(DISCORD_WEBHOOK_URL, json={"content": msg}) as resp:
                        logging.info(f"[enviar_a_discord] Webhook texto status: {resp.status}")
                        if resp.status == 200:
                            logging.info(f"✅ [Tg→Discord] Texto enviado via webhook")
                        else:
                            logging.error(f"❌ Webhook falló ({resp.status}), intentando canal...")
                            raise Exception("Webhook failed")
        else:
            # Método directo por canal
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
    except Exception as e:
        logging.error(f"❌ Error en enviar_a_discord: {e}")
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
            logging.error(f"❌ Error total enviando a Discord: {fallback_error}")

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
                    if resp.status == 200:
                        logging.info(f"✅ [Discord→Tg] Texto enviado: {message.content[:50]}...")
                    else:
                        error_text = await resp.text()
                        logging.error(f"❌ [Discord→Tg] Error {resp.status}: {error_text}")
        # Enviar archivos adjuntos
        for attachment in message.attachments:
            try:
                async with aiohttp.ClientSession() as session:
                    file_bytes = await attachment.read()
                    data = aiohttp.FormData()
                    data.add_field("chat_id", str(TELEGRAM_CHANNEL_ID))
                    # Determinar tipo de archivo
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

# ========== TELEGRAM → DISCORD ==========
@tg_dp.channel_post_handler()
async def debug_all_channel_posts(message: types.Message):
    logging.info(f"🐛 DEBUG - Canal post detectado:")
    logging.info(f"    RAW: {message}")
    logging.info(f"    Chat ID: {message.chat.id}")
    logging.info(f"    Chat title: {message.chat.title}")
    logging.info(f"    Text: {message.text}")
    logging.info(f"    Caption: {getattr(message, 'caption', None)}")
    logging.info(f"    Photo: {getattr(message, 'photo', [])}")
    logging.info(f"    Document: {getattr(message, 'document', None)}")
    logging.info(f"    TELEGRAM_CHANNEL_ID configurado: {TELEGRAM_CHANNEL_ID}")
    if message.chat.id == TELEGRAM_CHANNEL_ID:
        logging.info("✅ IDs coinciden - procesando mensaje...")
    else:
        logging.warning(f"⚠️ IDs diferentes. Esperado: {TELEGRAM_CHANNEL_ID}, Recibido: {message.chat.id}")

@tg_dp.channel_post_handler(chat_id=TELEGRAM_CHANNEL_ID)
async def telegram_to_discord(message: types.Message):
    logging.info(f"🎯 Handler canal activado - Chat: {message.chat.id}")
    try:
        logging.info("[Tg→Discord] Handler ENTRÓ al try.")
        # Texto plano (NO loops de Discord)
        logging.info(">> Antes del chequeo de texto")
        if message.text and not message.text.startswith('[Discord]'):
            logging.info(">> Antes de enviar_a_discord")
            msg = f"[Telegram] {message.text}"
            await enviar_a_discord(msg)
            logging.info(f"✅ [Tg→Discord] Texto enviado exitosamente: {message.text}")
        elif message.text and message.text.startswith('[Discord]'):
            logging.info(f"⏭️ Mensaje ignorado (proviene de Discord): {message.text}")
        else:
            logging.info("⏭️ Mensaje sin texto o vacío, revisando otros tipos...")

        # Foto
        if message.photo:
            try:
                logging.info(">> Foto detectada, procesando...")
                photo = message.photo[-1]
                file = await photo.download()
                caption = message.caption or "Imagen desde Telegram"
                msg = f"[Telegram] {caption}"
                await enviar_a_discord(msg, file_path=file.name, filename=f"telegram_image_{photo.file_id}.jpg")
                logging.info(f"✅ [Tg→Discord] Imagen enviada")
                try:
                    os.remove(file.name)
                except Exception:
                    pass
            except Exception as e:
                logging.error(f"❌ Error enviando imagen: {e}")

        # Documento
        if message.document:
            try:
                logging.info(">> Documento detectado, procesando...")
                file = await message.document.download()
                caption = message.caption or "Archivo desde Telegram"
                msg = f"[Telegram] {caption}"
                await enviar_a_discord(msg, file_path=file.name, filename=message.document.file_name)
                logging.info(f"✅ [Tg→Discord] Documento enviado")
                try:
                    os.remove(file.name)
                except Exception:
                    pass
            except Exception as e:
                logging.error(f"❌ Error enviando documento: {e}")

    except Exception as e:
        logging.error(f"❌ Error general en telegram_to_discord: {e}")
        import traceback
        logging.error(traceback.format_exc())

# ========== COMANDOS ÚTILES ==========
@tg_dp.message_handler(commands=["getid"])
async def cmd_getid(message: types.Message):
    try:
        chat = message.chat
        user = message.from_user
        info = f"📍 **INFORMACIÓN DEL CHAT**\n\n"
        info += f"🏷️ **Nombre:** {chat.title or chat.full_name or '(sin nombre)'}\n"
        info += f"🆔 **ID:** `{chat.id}`\n"
        info += f"📂 **Tipo:** {chat.type}\n"
        if chat.username:
            info += f"🔗 **Username:** @{chat.username}\n"
        if user:
            info += f"\n👤 **USUARIO**\n"
            info += f"🏷️ **Nombre:** {user.full_name}\n"
            info += f"🆔 **User ID:** `{user.id}`\n"
            if user.username:
                info += f"🔗 **Username:** @{user.username}\n"
        await message.reply(info, parse_mode='Markdown')
        logging.info(f"[CMD] /getid ejecutado - Chat: {chat.id} por {user.full_name if user else 'N/A'}")
    except Exception as e:
        error_msg = f"❌ Error obteniendo información: {e}"
        await message.reply(error_msg)
        logging.error(error_msg)

# ========== VERIFICACIÓN DE CONFIGURACIÓN ==========
async def verificar_configuracion():
    try:
        chat = await tg_bot.get_chat(TELEGRAM_CHANNEL_ID)
        logging.info(f"✅ Canal Telegram encontrado: {chat.title} ({chat.id})")
        try:
            member = await tg_bot.get_chat_member(TELEGRAM_CHANNEL_ID, tg_bot.id)
            logging.info(f"🤖 Bot status en canal: {member.status}")
            if member.status not in ['administrator', 'creator']:
                logging.warning("⚠️ ADVERTENCIA: El bot NO es administrador del canal")
        except Exception as e:
            logging.warning(f"⚠️ No se pudo verificar permisos del bot: {e}")
        if discord_bot.user:
            logging.info(f"✅ Discord bot conectado: {discord_bot.user}")
        else:
            logging.warning("⚠️ Discord bot no conectado aún")
        logging.info(f"🔧 Configuración:")
        logging.info(f"    Telegram Canal ID: {TELEGRAM_CHANNEL_ID}")
        logging.info(f"    Discord Canal ID: {DISCORD_CANAL_ID}")
        logging.info(f"    Webhook configurado: {'Sí' if DISCORD_WEBHOOK_URL else 'No'}")
    except Exception as e:
        logging.error(f"❌ Error verificando configuración: {e}")

# ========== MAIN ==========
async def main():
    logging.info("🚀 Iniciando integración Discord ↔️ Telegram...")
    try:
        await verificar_configuracion()
        logging.info("📡 Iniciando polling de Telegram...")
        tg_task = asyncio.create_task(tg_dp.start_polling())
        logging.info("🎮 Conectando bot de Discord...")
        dc_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
        await asyncio.gather(tg_task, dc_task)
    except Exception as e:
        logging.error(f"💥 Error fatal en main: {e}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        required_vars = [
            "DISCORD_TOKEN", "DISCORD_CANAL_TELEGRAM", 
            "TELEGRAM_TOKEN_INTEGRACION", "TELEGRAM_CHANNEL_ID"
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
