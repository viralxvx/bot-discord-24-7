from flask import Flask
from threading import Thread
import discord
import re
import os
import datetime
from discord.ext import commands

# ====== 1. TOKEN y CANAL OBJETIVO desde variables de entorno ======
TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]

# ====== 2. INTENTS Y BOT SETUP ======
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== 3. MENSAJE FIJO ======
MENSAJE_NORMAS = (
    "📌 Bienvenid@ al canal 🧵go-viral\n\n"
    "🔹 Reacciona con 🔥 a todas las publicaciones anteriores antes de publicar.\n"
    "🔹 Debes reaccionar a tu propia publicación con 👍.\n"
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

# ====== 5. BIENVENIDA ======
@bot.event
async def on_member_join(member):
    canal = discord.utils.get(member.guild.text_channels, name="👉preséntate")
    if canal:
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
        await canal.send(mensaje)

# ====== 6. FILTRO DE MENSAJES EN go-viral ======
@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.name != CANAL_OBJETIVO:
        return

    # Validar que solo haya un link y ningún texto
    urls = re.findall(r"https://x\\.com/[^\s]+", message.content)
    if not urls or len(urls) > 1 or len(message.content.strip()) != len(urls[0]):
        await message.delete()
        aviso = await message.channel.send(
            f"{message.author.mention} solo se permite **un link de X** sin texto adicional."
        )
        await aviso.delete(delay=15)
        return

    # Validar que no tenga parámetros
    if "?" in urls[0]:
        await message.delete()
        aviso = await message.channel.send(
            f"{message.author.mention} tu link contiene parámetros. Usa formato limpio."
        )
        await aviso.delete(delay=15)
        return

    # Recolectar mensajes anteriores (sin contar los del bot ni el actual)
    anteriores = []
    async for msg in message.channel.history(limit=100):
        if msg.id != message.id and msg.author != bot.user:
            anteriores.append(msg)

    # Verificar publicaciones del mismo autor
    propias = [m for m in anteriores if m.author == message.author]
    if propias:
        ultima = propias[0]
        diff = datetime.datetime.utcnow() - ultima.created_at.replace(tzinfo=None)
        otros = [m for m in anteriores if m.author != message.author]
        if len(otros) < 2 and diff.total_seconds() < 86400:
            await message.delete()
            aviso = await message.channel.send(
                f"{message.author.mention} debes esperar 2 publicaciones de otros o 24h."
            )
            await aviso.delete(delay=15)
            return

    # Verifica si reaccionó con 🔥 a todos los anteriores
    for msg in anteriores:
        apoyado = False
        for r in msg.reactions:
            if str(r.emoji) == "🔥":
                async for u in r.users():
                    if u == message.author:
                        apoyado = True
                        break
        if not apoyado:
            await message.delete()
            aviso = await message.channel.send(
                f"{message.author.mention} debes reaccionar con 🔥 a **todas** las publicaciones antes de publicar."
            )
            await aviso.delete(delay=15)
            return

    # Esperar unos segundos antes de validar 👍
    await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=5))
    valido = False
    mensaje_actual = await message.channel.fetch_message(message.id)
    for r in mensaje_actual.reactions:
        if str(r.emoji) == "👍":
            async for u in r.users():
                if u == message.author:
                    valido = True
                    break

    if not valido:
        await message.delete()
        aviso = await message.channel.send(
            f"{message.author.mention} debes reaccionar con 👍 a tu publicación."
        )
        await aviso.delete(delay=15)
        return

# ====== 7. KEEP ALIVE PARA RAILWAY ======
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
