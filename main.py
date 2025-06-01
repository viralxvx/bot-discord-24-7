from flask import Flask
from threading import Thread
import discord
import re
from discord.ext import commands
import os

# ====== 1. TOKEN y CANAL OBJETIVO desde variables de entorno ======
TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]

# ====== 2. INTENTS Y BOT SETUP ======
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== 3. MENSAJE FIJO ======
MENSAJE_NORMAS = (
    "📌 Bienvenid@ al canal 🧵go-viral\n\n"
    "🔹 Reacciona con 🔥 a al menos dos publicaciones anteriores antes de publicar.\n"
    "🔹 Solo se permiten enlaces de X (Twitter) con este formato:\n"
    "https://x.com/usuario/status/1234567890123456789\n"
    "(no debe contener signos de interrogación ni parámetros al final)\n\n"
    "❌ Publicaciones que no cumplan serán eliminadas automáticamente."
)

# ====== 4. CUANDO SE CONECTA ======
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == CANAL_OBJETIVO:
                async for msg in channel.history(limit=50):
                    if msg.author == bot.user:
                        await msg.delete()
                try:
                    msg = await channel.send(MENSAJE_NORMAS)
                    await msg.pin()
                except discord.Forbidden:
                    print("No tengo permisos para anclar el mensaje.")
                break

# ====== 5. MENSAJE DE BIENVENIDA AUTOMÁTICO ======
@bot.event
async def on_member_join(member):
    canal_presentate = discord.utils.get(member.guild.text_channels, name="👉preséntate")
    if canal_presentate:
        mensaje = (
            f"👋 ¡Bienvenid@ a **VX** {member.mention}!\n\n"
            "Te deseamos muchos éxitos creando contenido viral. 🎯\n\n"
            "✅ Para comenzar, por favor sigue estos pasos:\n"
            "1️⃣ Lee las 3 guías en 📖guías\n"
            "2️⃣ Revisa las normas en ✅normas-generales\n"
            "3️⃣ Inspírate con 🏆victorias\n"
            "4️⃣ Estudia las estrategias en ♟estrategias-probadas\n\n"
            "Cuando hayas terminado, ve a 🏋entrenamiento y solicita ayuda para crear tu primer post.\n\n"
            "¡Mucho éxito y a romperla! 🚀"
        )
        await canal_presentate.send(mensaje)

# ====== 6. FILTRO DE MENSAJES ======
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.name != CANAL_OBJETIVO:
        return

    # Verifica el formato del enlace de X (Twitter)
    urls = re.findall(r"https://x\.com/[^\s]+", message.content)
    for url in urls:
        if "?" in url:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} tu publicación fue eliminada porque el enlace de X contiene parámetros.\n"
                f"Utiliza solo el formato limpio como: https://x.com/usuario/status/1234567890123456789"
            )
            return

    # Obtiene las 2 publicaciones anteriores (sin contar el mensaje actual)
    mensajes_anteriores = []
    async for msg in message.channel.history(limit=50):
        if msg.id == message.id:
            continue
        if msg.author != bot.user:
            mensajes_anteriores.append(msg)
        if len(mensajes_anteriores) == 2:
            break

    if len(mensajes_anteriores) < 2:
        await message.delete()
        await message.channel.send(
            f"{message.author.mention} tu mensaje fue eliminado. Aún no hay suficientes publicaciones para reaccionar con 🔥."
        )
        return

    # Verifica que haya reaccionado con 🔥 a ambas
    reacciones_validas = 0
    for msg in mensajes_anteriores:
        reacciono = False
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🔥":
                async for user in reaction.users():
                    if user == message.author:
                        reacciono = True
                        break
            if reacciono:
                break
        if reacciono:
            reacciones_validas += 1

    if reacciones_validas < 2:
        await message.delete()
        await message.channel.send(
            f"{message.author.mention} tu mensaje fue eliminado. Debes reaccionar con 🔥 a las últimas 2 publicaciones antes de publicar."
        )
        return

    await bot.process_commands(message)

# ====== 7. KEEP ALIVE PARA SERVIDORES COMO RAILWAY ======
app = Flask('')

@app.route('/')
def home():
    return "El bot está corriendo!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(TOKEN)
