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

# ====== 5. MENSAJE DE BIENVENIDA ======
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

# ====== 6. FILTRO DE MENSAJES EN go-viral ======
@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.name != CANAL_OBJETIVO:
        return

    # 1. Verificar formato del link
    urls = re.findall(r"https://x\.com/[^\s]+", message.content)
    for url in urls:
        if "?" in url:
            await message.delete()
            advertencia = await message.channel.send(
                f"{message.author.mention} tu publicación fue eliminada porque el enlace de X contiene parámetros.\n"
                f"Usa este formato: https://x.com/usuario/status/1234567890123456789"
            )
            await advertencia.delete(delay=15)
            return

    # 2. Revisar publicaciones previas del canal
    mensajes = []
    async for msg in message.channel.history(limit=100):
        if msg.id == message.id:
            continue
        if msg.author != bot.user:
            mensajes.append(msg)

    # 3. Verifica si el usuario ya publicó recientemente
    publicaciones_usuario = [m for m in mensajes if m.author == message.author]
    if publicaciones_usuario:
        ultima_publicacion = publicaciones_usuario[0]
        ahora = datetime.datetime.utcnow()
        diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)

        # Verifica si hay al menos 2 publicaciones de otros usuarios después
        otros = [m for m in mensajes if m.author != message.author]
        if len(otros) < 2 and diferencia.total_seconds() < 86400:
            await message.delete()
            advertencia = await message.channel.send(
                f"{message.author.mention} aún no puedes publicar.\n"
                f"Debes esperar al menos 2 publicaciones de otros miembros o 24 horas desde tu última publicación."
            )
            await advertencia.delete(delay=15)
            return

    # 4. Verifica si el usuario ha reaccionado con 🔥 a todos los mensajes anteriores
    no_apoyados = []
    for msg in mensajes:
        apoyo = False
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🔥":
                async for user in reaction.users():
                    if user == message.author:
                        apoyo = True
                        break
        if not apoyo:
            no_apoyados.append(msg)

    if no_apoyados:
        await message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} debes reaccionar con 🔥 a **todas las publicaciones anteriores** antes de publicar."
        )
        await advertencia.delete(delay=15)
        return

    # 5. Verifica si reaccionó a su propio post con 👍
    await bot.process_commands(message)  # Procesar comandos primero

    def check_reaccion_propia(reaction, user):
        return (
            reaction.message.id == message.id and
            str(reaction.emoji) == "👍" and
            user == message.author
        )

    try:
        await bot.wait_for("reaction_add", timeout=60, check=check_reaccion_propia)
    except:
        await message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} tu publicación fue eliminada. Debes reaccionar con 👍 a tu propia publicación para validarla."
        )
        await advertencia.delete(delay=15)
        return

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
