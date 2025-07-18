# integraciones/telegram_discord.py

import os
import asyncio
import logging
from aiogram import Bot as TGBot, Dispatcher as TGDispatcher, types as tg_types
from discord.ext import commands
import discord
import aiohttp

# === LOGGING CONFIG ===
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger("TG-DC-sync")

# === VARIABLES DE ENTORNO ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_TELEGRAM = os.getenv("DISCORD_CANAL_TELEGRAM")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # Username SIN arroba

if not all([DISCORD_TOKEN, DISCORD_CANAL_TELEGRAM, TELEGRAM_TOKEN, TELEGRAM_CANAL]):
    log.error("❌ Faltan variables de entorno. Revisa que estén todas:")
    log.error("DISCORD_TOKEN, DISCORD_CANAL_TELEGRAM, TELEGRAM_TOKEN, TELEGRAM_CANAL")
    exit(1)

try:
    DISCORD_CANAL_TELEGRAM = int(DISCORD_CANAL_TELEGRAM)
except Exception as e:
    log.error(f"❌ DISCORD_CANAL_TELEGRAM debe ser el ID numérico del canal de Discord. Error: {e}")
    exit(1)

# === --- TELEGRAM A DISCORD --- ===

tg_bot = TGBot(token=TELEGRAM_TOKEN)
tg_dp = TGDispatcher(tg_bot)

# Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_bot = commands.Bot(command_prefix="!", intents=intents)

async def telegram_to_discord():
    @tg_dp.message_handler()
    async def handle_telegram_msg(message: tg_types.Message):
        if message.chat.type in ["group", "supergroup", "channel", "private"]:
            user = getattr(message.from_user, "full_name", "Anon")
            text = f"[TG] {user}: {message.text}"
            log.info(f"⬆️ [TELEGRAM] Mensaje recibido: {text}")

            await asyncio.sleep(2)  # Evita rate limit
            channel = discord_bot.get_channel(DISCORD_CANAL_TELEGRAM)
            if channel:
                await channel.send(text)
                log.info(f"➡️ [DISCORD] Mensaje reenviado a canal ID {DISCORD_CANAL_TELEGRAM}")
            else:
                log.error("❌ Canal de Discord no encontrado o bot no tiene acceso. Revisa el ID y los permisos.")
    await tg_dp.start_polling()

# === --- DISCORD A TELEGRAM --- ===

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != DISCORD_CANAL_TELEGRAM:
        return

    text = f"[Discord] {message.author.display_name}: {message.content}"
    log.info(f"⬆️ [DISCORD] Mensaje recibido: {text}")
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": f"@{TELEGRAM_CANAL}",
            "text": text
        }
        async with session.post(url, data=payload) as resp:
            if resp.status == 200:
                log.info(f"➡️ [TELEGRAM] Mensaje reenviado a canal @{TELEGRAM_CANAL}")
            else:
                err_text = await resp.text()
                log.error(f"❌ Error enviando mensaje a Telegram: {err_text}")
    await discord_bot.process_commands(message)

# === ARRANQUE ===

async def main():
    log.info("🔗 Sincronización Telegram <-> Discord corriendo...")
    await asyncio.gather(
        discord_bot.start(DISCORD_TOKEN),
        telegram_to_discord(),
    )

if __name__ == "__main__":
    asyncio.run(main())
