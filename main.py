import discord
from discord.ext import commands
from flask import Flask, jsonify
from threading import Thread
import os

from config import TOKEN, INTENTS, EXTENSIONS
from state_management import save_state
from redis_database import init_redis

bot = commands.Bot(command_prefix="!", intents=INTENTS)
app = Flask(__name__)

@app.route('/')
def home():
    return "El bot está corriendo!"

@app.route('/health')
def health():
    return jsonify({
        "status": "running",
        "bot_ready": bot.is_ready(),
    })

def run_webserver():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_webserver)
    t.daemon = True
    t.start()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# Cargar extensiones (módulos)
for extension in EXTENSIONS:
    try:
        bot.load_extension(extension)
        print(f"✅ Cargado módulo: {extension}")
    except Exception as e:
        print(f"❌ Error cargando {extension}: {e}")

if __name__ == "__main__":
    init_redis()
    keep_alive()
    bot.run(TOKEN)
