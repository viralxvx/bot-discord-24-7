import os
import json
import httpx
import asyncio
import logging
import discord
from discord.ext import commands

# ========== CONFIGURACIÓN ==========
TOKEN = os.getenv("DISCORD_TOKEN")
CANAL_GPT_ID = int(os.getenv("CANAL_GPT_ID"))

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vx-deepseek")

# ========== CLIENTE DISCORD ==========
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========== EVENTO: CONEXIÓN ==========
@bot.event
async def on_ready():
    logger.info(f"✅ vx-deepseek conectado como {bot.user}")

# ========== EVENTO: MENSAJE NUEVO ==========
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != CANAL_GPT_ID:
        return

    contenido = message.content.strip()
    autor = message.author.name
    logger.info(f"🧠 Solicitud de {autor}: {contenido}")

    await responder_con_deepseek(contenido, message)

# ========== FUNCION: ENVIAR A DEEPSEEK CHAT ==========
async def responder_con_deepseek(prompt, mensaje_original):
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.puter.com/v1/chat/completions", json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            texto = data["choices"][0]["message"]["content"]
            await mensaje_original.channel.send(f"💬 {texto}")
        else:
            logger.error(f"❌ Error {response.status_code}: {response.text}")
            await mensaje_original.channel.send("❌ No se pudo obtener respuesta de DeepSeek.")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        await mensaje_original.channel.send("❌ Ocurrió un error inesperado.")

# ========== INICIO ==========
if __name__ == "__main__":
    bot.run(TOKEN)
