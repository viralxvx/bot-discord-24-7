import os
import discord
import logging
import asyncio
import httpx

# ================= CONFIGURACIÓN =================
TOKEN = os.getenv("DISCORD_TOKEN")
CANAL_GPT_ID = int(os.getenv("CANAL_GPT_ID"))  
PUTER_API_URL = "https://api.puter.com/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}
MODEL = "deepseek-chat"  # Cambia aquí el modelo si quieres probar otro

# ================ LOGGING =======================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vx-deepseek")

# ================ CLIENTE DISCORD ================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ================ FUNCIÓN IA ======================
async def get_ai_response(prompt):
    try:
        async with httpx.AsyncClient() as client_http:
            res = await client_http.post(
                PUTER_API_URL,
                headers=HEADERS,
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30
            )
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                log.error(f"❌ Error {res.status_code}: {res.text}")
                return "Ocurrió un error con DeepSeek AI."
    except Exception as e:
        log.exception("Error al obtener respuesta de DeepSeek:")
        return "No se pudo procesar la solicitud."

# =============== EVENTO DE MENSAJE =================
@client.event
async def on_ready():
    log.info(f"✅ vx-deepseek conectado como {client.user}")

@client.event
async def on_message(message):
    if message.author.bot or message.channel.id != CANAL_GPT_ID:
        return

    prompt = message.content.strip()
    if not prompt:
        return

    log.info(f"🧠 Solicitud de {message.author.name}: {prompt}")
    async with message.channel.typing():
        respuesta = await get_ai_response(prompt)
        await message.reply(respuesta[:1900], mention_author=False)

# ================== INICIAR BOT ====================
if __name__ == "__main__":
    if not TOKEN or not CANAL_GPT_ID:
        log.error("❌ Faltan variables de entorno requeridas.")
    else:
        client.run(TOKEN)
