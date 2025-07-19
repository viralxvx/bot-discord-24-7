# integraciones/telegram_discord.py

import os
import asyncio
import discord
import aiohttp
from aiogram import Bot as TGBot, Dispatcher as TGDispatcher, types as tg_types
from aiogram.utils import executor

# === VARIABLES DE ENTORNO ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CANAL_TELEGRAM = int(os.getenv("DISCORD_CANAL_TELEGRAM"))  # ID del canal en Discord
TELEGRAM_TOKEN_INTEGRACION = os.getenv("TELEGRAM_TOKEN_INTEGRACION")  # Token del bot espejo de Telegram
TELEGRAM_CANAL = os.getenv("TELEGRAM_CANAL")  # Username SIN arroba, ej: viralxvx

if not DISCORD_TOKEN or not DISCORD_CANAL_TELEGRAM or not TELEGRAM_TOKEN_INTEGRACION or not TELEGRAM_CANAL:
    raise Exception("❌ Faltan variables de entorno para la integración Telegram <-> Discord")

# === --- TELEGRAM A DISCORD --- ===
tg_bot = TGBot(token=TELEGRAM_TOKEN_INTEGRACION)
tg_dp = TGDispatcher(tg_bot)

# Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_bot = discord.Client(intents=intents)

async def telegram_to_discord():
    @tg_dp.message_handler()
    async def handle_telegram_msg(message: tg_types.Message):
        # SOLO MENSAJES DEL CANAL configurado (no grupos, no privados)
        if message.chat.type == "channel" and message.chat.username and message.chat.username.lower() == TELEGRAM_CANAL.lower():
            text = f"[TG canal] {message.chat.title or TELEGRAM_CANAL}: {message.text}"
        else:
            # Opcional: Loguea intentos de otros chats, no envíes nada.
            print(f"⚠️ Mensaje ignorado de chat {message.chat.id} tipo {message.chat.type}")
            return

        # Enviar a Discord
        await asyncio.sleep(1)  # Pequeña pausa para evitar rate limit
        channel = discord_bot.get_channel(DISCORD_CANAL_TELEGRAM)
        if channel:
            await channel.send(text)
            print(f"✅ Telegram → Discord: {text}")
        else:
            print("❌ Canal de Discord no encontrado.")

    await tg_dp.start_polling()

# === --- DISCORD A TELEGRAM --- ===
@discord_bot.event
async def on_ready():
    print(f"✅ Discord ↔ Telegram integración activa como {discord_bot.user}")

@discord_bot.event
async def on_message(message):
    if message.author.bot:
        return  # No repitas mensajes de bots (ni el tuyo)
    if message.channel.id != DISCORD_CANAL_TELEGRAM:
        return  # Solo replica del canal configurado

    text = f"[Discord] {message.author.display_name}: {message.content}"
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN_INTEGRACION}/sendMessage"
        payload = {
            "chat_id": f"@{TELEGRAM_CANAL}",
            "text": text
        }
        async with session.post(url, data=payload) as resp:
            if resp.status == 200:
                print(f"✅ Discord → Telegram: {text}")
            else:
                print(f"❌ Error enviando a Telegram: {await resp.text()}")

# === ARRANQUE ===
async def main():
    print("🔗 Integración Discord ↔ Telegram corriendo...")
    await asyncio.gather(
        discord_bot.start(DISCORD_TOKEN),
        telegram_to_discord()
    )

if __name__ == "__main__":
    asyncio.run(main())
