from flask import Flask
from threading import Thread
import discord
import re
import os
import datetime
from discord.ext import commands

TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

MENSAJE_NORMAS = (
    "📌 Bienvenid@ al canal 🧵go-viral\n\n"
    "🔹 Reacciona con 🔥 a todas las publicaciones desde tu última publicación antes de volver a publicar.\n"
    "🔹 Debes reaccionar a tu propia publicación con 👍.\n"
    "🔹 Solo se permiten enlaces de X (Twitter) con este formato:\n"
    "https://x.com/usuario/status/1234567890123456789\n"
    "❌ Publicaciones con texto adicional o formato incorrecto serán eliminadas."
)

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

@bot.event
async def on_member_join(member):
    canal_presentate = discord.utils.get(member.guild.text_channels, name="👉preséntate")
    if canal_presentate:
        mensaje = (
            f"👋 ¡Bienvenid@ a **VX** {member.mention}!\n\n"
            "Sigue estos pasos:\n"
            "📖 Lee las 3 guías\n"
            "✅ Revisa las normas\n"
            "🏆 Mira las victorias\n"
            "♟ Estudia las estrategias\n"
            "🏋 Luego solicita ayuda para tu primer post."
        )
        await canal_presentate.send(mensaje)

@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.name != CANAL_OBJETIVO:
        return

    # Validar link de X y que sea el único contenido
    urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
    if len(urls) != 1 or "?" in urls[0] or message.content.strip() != urls[0]:
        await message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} solo se permite **un link válido de X** sin texto adicional.\nFormato: https://x.com/usuario/status/1234567890123456789"
        )
        await advertencia.delete(delay=15)
        return

    # Obtener mensajes anteriores
    mensajes = []
    async for msg in message.channel.history(limit=100):
        if msg.id == message.id or msg.author == bot.user:
            continue
        mensajes.append(msg)

    # Buscar última publicación del usuario
    ultima_publicacion = None
    for msg in mensajes:
        if msg.author == message.author:
            ultima_publicacion = msg
            break

    # Si no tiene publicaciones anteriores, permitir (primera vez)
    if not ultima_publicacion:
        await bot.process_commands(message)
        return

    # Verificar si hay al menos 2 publicaciones de otros miembros o han pasado 24h
    ahora = datetime.datetime.utcnow()
    diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
    publicaciones_despues = [m for m in mensajes if m.created_at > ultima_publicacion.created_at and m.author != message.author]
    if len(publicaciones_despues) < 2 and diferencia.total_seconds() < 86400:
        await message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} aún no puedes publicar.\nDebes esperar al menos 2 publicaciones de otros miembros o 24 horas desde tu última publicación."
        )
        await advertencia.delete(delay=15)
        return

    # Verificar que haya reaccionado con 🔥 a TODAS las publicaciones desde su última
    no_apoyados = []
    for msg in mensajes:
        if msg.created_at <= ultima_publicacion.created_at:
            break  # Solo revisar desde su última publicación hacia adelante
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
            f"{message.author.mention} debes reaccionar con 🔥 a **todas las publicaciones desde tu última publicación** antes de publicar."
        )
        await advertencia.delete(delay=15)
        return

    # Esperar reacción 👍 en su propio mensaje
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

# ✅ NUEVO EVENTO: RESTRICCIÓN DE REACCIONES
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.message.channel.name != CANAL_OBJETIVO:
        return

    autor = reaction.message.author
    emoji_valido = "👍" if user == autor else "🔥"

    if str(reaction.emoji) != emoji_valido:
        await reaction.remove(user)
        advertencia = await reaction.message.channel.send(
            f"{user.mention} solo se permite reaccionar con {emoji_valido} en este canal."
        )
        await advertencia.delete(delay=15)

# ====== KEEP ALIVE ======
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
