import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import aiohttp
import discord

# === Variables de entorno ===
TELEGRAM_TOKEN_INTEGRACION = os.getenv("TELEGRAM_TOKEN_INTEGRACION")  # Token del bot espejo SOLO para integración
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # username, ej: viralxvx
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Webhook completo de Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Token del bot de Discord
DISCORD_CANAL_TELEGRAM = int(os.getenv("DISCORD_CANAL_TELEGRAM"))  # ID del canal de Discord a escuchar

# === Check ===
if not (TELEGRAM_TOKEN_INTEGRACION and TELEGRAM_CANAL and DISCORD_WEBHOOK_URL and DISCORD_TOKEN and DISCORD_CANAL_TELEGRAM):
    raise Exception("❌ Faltan variables de entorno para integración completa")

# === Telegram → Discord (canal Telegram → webhook Discord) ===
tg_bot = Bot(token=TELEGRAM_TOKEN_INTEGRACION)
tg_dp = Dispatcher(tg_bot)

@tg_dp.message_handler()
async def handle_telegram_msg(message: types.Message):
    # Solo mensajes del canal público
    if message.chat.type == "channel" and message.chat.username and message.chat.username.lower() == TELEGRAM_CANAL.lower():
        text = f"**[Telegram]**\n{message.text or '[mensaje no textual]'}"
        async with aiohttp.ClientSession() as session:
            payload = {"content": text}
            async with session.post(DISCORD_WEBHOOK_URL, json=payload) as resp:
                if resp.status in [200, 204]:
                    print(f"✅ Telegram → Discord (webhook): {text}")
                else:
                    print(f"❌ Error webhook Discord: {await resp.text()}")
    else:
        # No publicar mensajes de grupos, otros canales, ni privados
        print(f"⚠️ Mensaje ignorado de chat {message.chat.id} tipo {message.chat.type}")

async def telegram_polling():
    print("▶️ Escuchando canal Telegram → Discord...")
    await tg_dp.start_polling()

# === Discord → Telegram (canal Discord → canal Telegram) ===
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_bot = discord.Client(intents=intents)

@discord_bot.event
async def on_ready():
    print(f"✅ Discord ↔ Telegram integración activa como {discord_bot.user}")

@discord_bot.event
async def on_message(message):
    # Ignora bots y solo escucha canal objetivo
    if message.author.bot:
        return
    if message.channel.id != DISCORD_CANAL_TELEGRAM:
        return
    # Envía a Telegram canal público
    text = f"[Discord] {message.author.display_name}: {message.content}"
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN_INTEGRACION}/sendMessage"
        payload = {
            "chat_id": f"@{TELEGRAM_CANAL}",  # username SIN @
            "text": text
        }
        async with session.post(url, data=payload) as resp:
            if resp.status == 200:
                print(f"✅ Discord → Telegram: {text}")
            else:
                print(f"❌ Error al enviar Discord → Telegram: {await resp.text()}")

async def main():
    await asyncio.gather(
        telegram_polling(),
        discord_bot.start(DISCORD_TOKEN)
    )

if __name__ == "__main__":
    print("🔗 Integración Discord ↔ Telegram corriendo...")
    asyncio.run(main())
