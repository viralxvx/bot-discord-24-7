from flask import Flask
from threading import Thread
import discord
import re
import os
import datetime
from discord.ext import commands, tasks
from collections import defaultdict

TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]
CANAL_LOGS = "📝logs"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"

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

ultima_publicacion_dict = {}
amonestaciones = defaultdict(list)

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
    verificar_inactividad.start()

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

async def registrar_log(texto):
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if canal_log:
        await canal_log.send(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {texto}")

@tasks.loop(hours=24)
async def verificar_inactividad():
    canal = discord.utils.get(bot.get_all_channels(), name=CANAL_OBJETIVO)
    ahora = datetime.datetime.utcnow()
    for miembro in canal.members:
        if miembro.bot:
            continue
        ultima = ultima_publicacion_dict.get(miembro.id)
        if not ultima:
            ultima = ahora - datetime.timedelta(days=4)
        dias_inactivo = (ahora - ultima).days
        if dias_inactivo >= 6:
            await canal.guild.kick(miembro, reason="Expulsado por 6 días de inactividad tras baneo.")
            await miembro.send("Has sido **expulsado permanentemente** por reincidir en la inactividad.")
            await registrar_log(f"🔴 {miembro.name} fue expulsado por reincidir tras baneo.")
        elif dias_inactivo >= 3:
            role = discord.utils.get(canal.guild.roles, name="baneado")
            if role:
                await miembro.add_roles(role, reason="Inactividad por más de 3 días.")
                await miembro.send("Has sido **baneado por 7 días** por no publicar en 🧵go-viral.")
                await registrar_log(f"🟠 {miembro.name} fue baneado por inactividad.")

@bot.event
async def on_message(message):
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        def check(m): return m.author == message.author and m.channel == message.channel

        await message.channel.send("¿A quién deseas reportar? Menciona al usuario.")
        nombre_msg = await bot.wait_for("message", check=check, timeout=60)
        reportado = nombre_msg.mentions[0] if nombre_msg.mentions else None
        if not reportado:
            return await message.channel.send("❌ Usuario no reconocido.")

        await message.channel.send("¿Qué norma está violando? (RT, LIKE, COMENTARIO, FORMATO)")
        razon_msg = await bot.wait_for("message", check=check, timeout=60)
        razon = razon_msg.content.strip()

        amonestaciones[reportado.id].append(datetime.datetime.utcnow())
        cantidad = len([a for a in amonestaciones[reportado.id] if datetime.datetime.utcnow() - a < datetime.timedelta(days=7)])

        if cantidad >= 6:
            await message.guild.kick(reportado, reason="Expulsado tras múltiples amonestaciones.")
            await reportado.send("Has sido **expulsado permanentemente** tras múltiples reportes acumulados.")
            await registrar_log(f"🔴 {reportado.name} fue expulsado tras 6 reportes en una semana.")
        elif cantidad == 3:
            role = discord.utils.get(message.guild.roles, name="baneado")
            if role:
                await reportado.add_roles(role, reason="3 amonestaciones en una semana.")
            await reportado.send("Has sido **baneado por 7 días** tras 3 reportes en una semana.")
            await registrar_log(f"🟠 {reportado.name} fue baneado por 3 amonestaciones.")
        else:
            await reportado.send(f"⚠️ Has recibido una amonestación por: {razon}")
            await registrar_log(f"⚠️ {reportado.name} recibió amonestación por: {razon}")
        return

    if message.author == bot.user or message.channel.name != CANAL_OBJETIVO:
        return

    # Extract URLs from the message, excluding query parameters
    urls = re.findall(r"https://x\.com/[^\s?]+", message.content.strip())
    
early access to Grok 3.5, and I don’t have information on its availability, so this code is tailored for your current setup with Grok 3.

### Deployment Notes for GitHub and Railway
Since you’re using GitHub and Railway, here are a few tips to ensure smooth deployment:
1. **Environment Variables**: Ensure `TOKEN` and `CANAL_OBJETIVO` are correctly set in Railway’s environment variables. You can configure these in the Railway dashboard under your project’s settings.
2. **Dependencies**: Make sure your `requirements.txt` includes the necessary packages. For this code, you need:
