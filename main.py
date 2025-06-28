from flask import Flask
from threading import Thread
import discord
import re
import os
import datetime
from discord.ext import commands, tasks
from collections import defaultdict
from discord.ui import View, Select
from discord import SelectOption, Interaction

TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]
CANAL_LOGS = "📝logs"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "👨🔧soporte"
CANAL_FLUJO_SOPORTE = "flujo-de-soporte"  # Canal para FAQs
ADMIN_ID = os.environ.get("ADMIN_ID", "1174775323649392844")  # Valor por defecto
INACTIVITY_TIMEOUT = 300  # 5 minutos en segundos

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

MENSAJE_NORMAS = (
    "📌 Bienvenid@ al canal 🧵go-viral\n\n"
    "🔹 Reacciona con 🔥 a todas las publicaciones de otros miembros desde tu última publicación antes de volver a publicar.\n"
    "🔹 Debes reaccionar a tu propia publicación con 👍.\n"
    "🔹 Solo se permiten enlaces de X (Twitter) con este formato:\n"
    "https://x.com/usuario/status/1234567890123456789\n"
    "❌ Publicaciones con texto adicional o formato incorrecto serán eliminadas."
)

ultima_publicacion_dict = {}
amonestaciones = defaultdict(list)
baneos_temporales = defaultdict(lambda: None)
ticket_counter = 0  # Contador para tickets
active_conversations = {}  # Diccionario para rastrear conversaciones activas {user_id: {"message_ids": [], "last_time": datetime}}
faq_data = {}  # Diccionario para almacenar preguntas y respuestas del canal flujo-de-soporte

# Respuestas predefinidas como fallback si no están en flujo-de-soporte
FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": "VX es una comunidad donde crecemos apoyándonos. Tú apoyas, y luego te apoyan. Publicas tu post después de apoyar a los demás. 🔥 = apoyaste, 👍 = tu propio post.",
    "✅ ¿Cómo publico mi post?": "Para publicar: 1️⃣ Apoya todos los posts anteriores (like + RT + comentario) 2️⃣ Reacciona con 🔥 en Discord 3️⃣ Luego publica tu post y colócale 👍. No uses 🔥 en tu propio post.",
    "✅ ¿Cómo subo de nivel?": "Subes de nivel participando activamente, apoyando a todos y siendo constante. Los niveles traen beneficios como prioridad, mentoría y más."
}

@bot.event
async def on_ready():
    global ticket_counter, faq_data
    print(f"Bot conectado como {bot.user}")
    await registrar_log(f"Bot iniciado. ADMIN_ID cargado: {ADMIN_ID}")
    # Cargar FAQ desde el canal flujo-de-soporte
    canal_flujo = discord.utils.get(bot.get_all_channels(), name=CANAL_FLUJO_SOPORTE)
    if canal_flujo:
        async for msg in canal_flujo.history(limit=100):
            if msg.author == bot.user and msg.pinned:
                lines = msg.content.split("\n")
                question = None
                response = []
                for line in lines:
                    if line.startswith("**Pregunta:**"):
                        question = line.replace("**Pregunta:**", "").strip()
                    elif line.startswith("**Respuesta:**"):
                        response = [line.replace("**Respuesta:**", "").strip()]
                    elif question and not line.startswith("**"):
                        response.append(line.strip())
                if question and response:
                    faq_data[question] = "\n".join(response)
    # Usar fallback si no hay datos en el canal
    if not faq_data:
        faq_data.update(FAQ_FALLBACK)
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
            elif channel.name == CANAL_REPORTES:
                async for msg in channel.history(limit=20):
                    if msg.author == bot.user and msg.pinned:
                        await msg.unpin()
                fijado = await channel.send(
