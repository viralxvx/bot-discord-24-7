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
    "❌ Publicaciones con texto adicional o formato incorrecto serán eliminadas."
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

# ====== 5. BIENVENIDA NUEVOS USUARIOS ======
@bot.event
async def on_member_join(member):
    canal_presentate = discord.utils.get(member.guild.text_channels, name="👉preséntate")
    if canal_presentate:
        mensaje = (
            f"👋 ¡Bienvenid@ a **VX** {member.mention}!\n\n"
            "✅ Sigue estos pasos:\n"
            "📖 Lee las 3 guías\n"
            "✅ Revisa las normas\n"
            "🏆 Mira las victorias\n"
            "♟ Estudia las estrategias\n"
            "🏋 Luego solicita ayuda para tu primer post."
        )
        await canal_presentate.send(mensaje)

# ====== 6. FILTRO DE MENSAJES Y REACCIONES ======
@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.name != CANAL_OBJETIVO:
        return

    # 1. Verificar que el mensaje SOLO contenga un link de X válido (sin texto)
    urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
    if len(urls) != 1 or "?" in urls[0] or message.content.strip() != urls[0]:
        await message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} solo se permite **un link válido de X** sin texto adicional.\nFormato: https://x.com/usuario/status/1234567890123456789"
        )
        await advertencia.delete(delay=15)
        return

    # 2. Revisar historial de mensajes
    mensajes = []
    async for msg in message.channel.history(limit=100):
        if msg.id == message.id:
            continue
        if msg.author != bot.user:
            mensajes.append(msg)

    # 3. Revisar si el usuario ya publicó recientemente
    publicaciones_usuario = [m for m in mensajes if m.author == message.author]
    if publicaciones_usuario:
        ultima_publicacion = publicaciones_usuario[0]
        ahora = datetime.datetime.utcnow()
        diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
        otros = [m for m in mensajes if m.author != message.author]
        if len(otros) < 2 and diferencia.total_seconds() < 86400:
            await message.delete()
            advertencia = await message.channel.send(
                f"{message.author.mention} aún no puedes publicar.\n"
                f"Debes esperar al menos 2 publicaciones de otros miembros o 24 horas desde tu última publicación."
            )
            await advertencia.delete(delay=15)
            return

    # 4. Verificar que ha reaccionado con 🔥 a todas las publicaciones anteriores
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

    # 5. Esperar reacción 👍 en su propio mensaje (1 minuto)
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
            f"{message.author.mention} tu publicación fue eliminada.\nDebes reaccionar con 👍 a tu propio mensaje para validarlo."
        )
        await advertencia.delete(delay=15)
        return

    await bot.process_commands(message)

# 7. RESTRINGE REACCIONES PERMITIDAS
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    if reaction.message.channel.name != CANAL_OBJETIVO:
        return

    autor = reaction.message.author

    # Solo 🔥 de OTROS usuarios a publicaciones de otros
    if user == autor:
        if str(reaction.emoji) != "👍":
            await reaction.remove(user)
    else:
        if str(reaction.emoji) != "🔥":
            await reaction.remove(user)

# ====== 8. KEEP ALIVE PARA RAILWAY ======
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
