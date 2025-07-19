# integraciones/telegram_discord_bridge.py

import os
import logging
import asyncio
import discord
from discord.ext import commands
from aiogram import Bot, Dispatcher, types
import aiohttp

# ========== CONFIG & VALIDACIÓN DE VARIABLES ==========
def get_env(name, required=True):
    value = os.getenv(name)
    if required and (value is None or value.strip() == ""):
        raise Exception(f"❌ FALTA VARIABLE DE ENTORNO: {name}")
    return value.strip() if value else value

DISCORD_TOKEN = get_env("DISCORD_TOKEN")
DISCORD_WEBHOOK_URL = get_env("DISCORD_WEBHOOK_URL")
TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN_INTEGRACION")
TELEGRAM_CHANNEL_ID = int(get_env("TELEGRAM_CHANNEL_ID"))

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

# ========== UTILITY: ENVIAR A DISCORD SOLO POR WEBHOOK ==========
async def enviar_a_discord(msg, file_path=None, filename=None):
    logging.info(f"[enviar_a_discord] INICIO. msg: {msg}, file: {file_path}")
    try:
        if not DISCORD_WEBHOOK_URL:
            logging.error("❌ No se configuró el webhook de Discord.")
            return

        async with aiohttp.ClientSession() as session:
            if file_path and filename:
                with open(file_path, "rb") as f:
                    form = aiohttp.FormData()
                    form.add_field("content", msg)
                    form.add_field("file", f, filename=filename)
                    async with session.post(DISCORD_WEBHOOK_URL, data=form) as resp:
                        text = await resp.text()
                        if resp.status in (200, 204):
                            logging.info(f"✅ [Tg→Discord] Archivo enviado via webhook. Status: {resp.status}")
                        else:
                            logging.error(f"❌ Webhook falló al enviar archivo. Status: {resp.status}, Resp: {text}")
            else:
                async with session.post(DISCORD_WEBHOOK_URL, json={"content": msg}) as resp:
                    text = await resp.text()
                    if resp.status in (200, 204):
                        logging.info(f"✅ [Tg→Discord] Texto enviado via webhook. Status: {resp.status}")
                    else:
                        logging.error(f"❌ Webhook falló al enviar texto. Status: {resp.status}, Resp: {text}")

    except Exception as e:
        logging.error(f"❌ Error en enviar_a_discord: {e}")

# ========== DISCORD → TELEGRAM ==========
@discord_bot.event
async def on_ready():
    logging.info(f"✅ Discord bot conectado como {discord_bot.user}")
    logging.info(f"🔗 Integrando canal Discord ↔️ Telegram {TELEGRAM_CHANNEL_ID}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Solo recibe desde canal configurado
    # (Deshabilitado: No hay canal directo, solo webhook)
    pass  # No implementado

# ========== TELEGRAM → DISCORD (CANAL TELEGRAM) ==========
@tg_dp.channel_post_handler()
async def debug_all_channel_posts(message: types.Message):
    logging.info(f"🐛 DEBUG - Canal post detectado:")
    logging.info(f"    RAW: {message}")
    logging.info(f"    Chat ID: {message.chat.id}")
    logging.info(f"    Chat title: {message.chat.title}")
    logging.info(f"    Text: {message.text}")
    logging.info(f"    Caption: {message.caption}")
    logging.info(f"    Photo: {message.photo}")
    logging.info(f"    Document: {message.document}")
    logging.info(f"    TELEGRAM_CHANNEL_ID configurado: {TELEGRAM_CHANNEL_ID}")
    if message.chat.id == TELEGRAM_CHANNEL_ID:
        logging.info("✅ IDs coinciden - procesando mensaje canal principal...")
    else:
        logging.warning(f"⚠️ IDs diferentes. Esperado: {TELEGRAM_CHANNEL_ID}, Recibido: {message.chat.id}")

@tg_dp.channel_post_handler(chat_id=TELEGRAM_CHANNEL_ID)
async def telegram_to_discord(message: types.Message):
    logging.info(f"🎯 Handler canal ACTIVADO - Chat: {message.chat.id}")
    try:
        # TEXTO
        if message.text and not message.text.startswith('[Discord]'):
            logging.info(">> Antes de enviar_a_discord (texto)")
            msg = f"[Telegram] {message.text}"
            await enviar_a_discord(msg)
            logging.info(f"✅ [Tg→Discord] Texto enviado exitosamente: {message.text}")

        elif message.text and message.text.startswith('[Discord]'):
            logging.info(f"⏭️ Mensaje ignorado (proviene de Discord)")

        # FOTOS
        if message.photo:
            photo = message.photo[-1]
            file = await photo.download()
            caption = message.caption or "Imagen desde Telegram"
            msg = f"[Telegram] {caption}"
            logging.info(">> Antes de enviar_a_discord (foto)")
            await enviar_a_discord(msg, file_path=file.name, filename=f"telegram_image_{photo.file_id}.jpg")
            logging.info(f"✅ [Tg→Discord] Imagen enviada")
            try:
                os.remove(file.name)
            except:
                pass

        # DOCUMENTOS
        if message.document:
            file = await message.document.download()
            caption = message.caption or "Archivo desde Telegram"
            msg = f"[Telegram] {caption}"
            logging.info(">> Antes de enviar_a_discord (documento)")
            await enviar_a_discord(msg, file_path=file.name, filename=message.document.file_name)
            logging.info(f"✅ [Tg→Discord] Documento enviado")
            try:
                os.remove(file.name)
            except:
                pass

    except Exception as e:
        logging.error(f"❌ Error general en telegram_to_discord: {e}")
        import traceback
        logging.error(traceback.format_exc())

# ========== COMANDOS DE UTILIDAD (getid, status, etc.) ==========
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

@tg_dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    try:
        status = f"🔗 **ESTADO DE INTEGRACIÓN**\n\n"
        status += f"📺 **Canal Telegram:** {TELEGRAM_CHANNEL_ID}\n"
        status += f"🌐 **Webhook:** {'✅ Configurado' if DISCORD_WEBHOOK_URL else '❌ No configurado'}\n"
        status += f"🤖 **Bot Status:** ✅ Activo\n"
        status += f"📊 **Funciones:**\n"
        status += f"• Telegram → Discord: ✅\n"
        status += f"• Archivos/Imágenes: ✅\n"
        await message.reply(status, parse_mode='Markdown')
        logging.info(f"[CMD] /status ejecutado")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        logging.error(f"[CMD] Error en /status: {e}")

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
        logging.info(f"🔧 Configuración:")
        logging.info(f"    Telegram Canal ID: {TELEGRAM_CHANNEL_ID}")
        logging.info(f"    Webhook configurado: {'Sí' if DISCORD_WEBHOOK_URL else 'No'}")
    except Exception as e:
        logging.error(f"❌ Error verificando configuración: {e}")

# ========== MAIN ==========
async def main():
    logging.info("🚀 Iniciando integración Discord ↔️ Telegram...")
    await verificar_configuracion()
    logging.info("📡 Iniciando polling de Telegram...")
    tg_task = asyncio.create_task(tg_dp.start_polling())
    logging.info("🎮 Conectando bot de Discord...")
    dc_task = asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
    await asyncio.gather(tg_task, dc_task)

if __name__ == "__main__":
    try:
        required_vars = [
            "DISCORD_TOKEN",
            "DISCORD_WEBHOOK_URL",
            "TELEGRAM_TOKEN_INTEGRACION",
            "TELEGRAM_CHANNEL_ID"
        ]
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        if missing_vars:
            logging.error(f"❌ FALTAN VARIABLES DE ENTORNO: {', '.join(missing_vars)}")
            exit(1)
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Bot detenido por el usuario")
    except Exception as e:
        logging.error(f"💥 Error crítico: {e}")
        import traceback
        logging.error(traceback.format_exc())
        exit(1)
