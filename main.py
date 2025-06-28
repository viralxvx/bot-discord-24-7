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
intents.members = True  # Asegura que el bot pueda ver miembros y menciones
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
            "👋 ¡Bienvenid@ a **VX** {member.mention}!\n\n"
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
    else:
        print(f"Log channel {CANAL_LOGS} not found: {texto}")  # Depuración si el canal no existe

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
        await registrar_log(f"Debug: Received message content: '{nombre_msg.content}'")
        await registrar_log(f"Debug: Raw mentions: {nombre_msg.raw_mentions}")
        await registrar_log(f"Debug: Mentions object: {nombre_msg.mentions}")
        reportado = next((m for m in nombre_msg.mentions), None)
        if not reportado:
            username = nombre_msg.content.replace("@", "").split("#")[0]
            reportado = discord.utils.get(message.guild.members, name=username)
            await registrar_log(f"Debug: Attempted username search for: '{username}'")
        if not reportado:
            await message.channel.send("❌ Usuario no reconocido. Asegúrate de mencionar a un usuario válido con @nombre.")
            await registrar_log(f"Debug: Failed to recognize user from content: '{nombre_msg.content}'")
            return

        await registrar_log(f"Debug: User identified: {reportado.name} (ID: {reportado.id})")
        await message.channel.send("¿Qué norma está violando? (RT, LIKE, COMENTARIO, FORMATO)")
        razon_msg = await bot.wait_for("message", check=check, timeout=60)
        razon = razon_msg.content.strip()
        await registrar_log(f"Debug: Received violation: '{razon}'")

        # Usar reportado directamente sin reevaluar
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

    # Extract URLs from the message
    urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
    
    # Check if there's exactly one URL and no additional text
    if len(urls) != 1 or (len(urls) == 1 and message.content.strip() != urls[0]):
        await message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} solo se permite **un link válido de X** sin texto adicional.\nFormato: https://x.com/usuario/status/1234567890123456789"
        )
        await advertencia.delete(delay=15)
        return

    # Clean the URL by removing query parameters
    url = urls[0].split('?')[0]  # Take only the base URL before '?'
    
    # Validate the URL format (e.g., https://x.com/username/status/1234567890123456789)
    url_pattern = r"https://x\.com/[^/]+/status/\d+"
    if not re.match(url_pattern, url):
        await message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} el enlace no tiene el formato correcto.\nFormato: https://x.com/usuario/status/1234567890123456789"
        )
        await advertencia.delete(delay=15)
        return

    # Optional: Log if the URL was cleaned (had query parameters)
    if '?' in urls[0]:
        await registrar_log(f"URL cleaned from {urls[0]} to {url} for user {message.author.name}")

    # Delete the original message and repost with the cleaned URL
    await message.delete()
    new_message = await message.channel.send(url)

    mensajes = []
    async for msg in message.channel.history(limit=100):
        if msg.id == new_message.id or msg.author == bot.user:
            continue
        mensajes.append(msg)

    ultima_publicacion = None
    for msg in mensajes:
        if msg.author == message.author:
            ultima_publicacion = msg
            break

    if not ultima_publicacion:
        ultima_publicacion_dict[message.author.id] = datetime.datetime.utcnow()
        await bot.process_commands(message)
        return

    ahora = datetime.datetime.utcnow()
    diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
    publicaciones_despues = [m for m in mensajes if m.created_at > ultima_publicacion.created_at and m.author != message.author]
    if len(publicaciones_despues) < 2 and diferencia.total_seconds() < 86400:
        await new_message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} aún no puedes publicar.\nDebes esperar al menos 2 publicaciones de otros miembros o 24 horas desde tu última publicación."
        )
        await advertencia.delete(delay=15)
        return

    no_apoyados = []
    for msg in mensajes:
        if msg.created_at <= ultima_publicacion.created_at:
            break
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
        await new_message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} debes reaccionar con 🔥 a **todas las publicaciones desde tu última publicación** antes de publicar."
        )
        await advertencia.delete(delay=15)

        urls_faltantes = [m.jump_url for m in no_apoyados]
        mensaje = (
            f"👋 {message.author.mention}, te faltan reacciones con 🔥 a los siguientes posts para poder publicar:\n" +
            "\n".join(urls_faltantes)
        )
        await message.author.send(mensaje)
        await registrar_log(f"{message.author.name} intentó publicar sin reaccionar a {len(no_apoyados)} publicaciones.")
        return

    def check_reaccion_propia(reaction, user):
        return (
            reaction.message.id == new_message.id and
            str(reaction.emoji) == "👍" and
            user == message.author
        )

    try:
        await bot.wait_for("reaction_add", timeout=60, check=check_reaccion_propia)
    except:
        await new_message.delete()
        advertencia = await message.channel.send(
            f"{message.author.mention} tu publicación fue eliminada.\nDebes reaccionar con 👍 a tu propio mensaje para validarlo."
        )
        await advertencia.delete(delay=15)
        return

    ultima_publicacion_dict[message.author.id] = datetime.datetime.utcnow()
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.message.channel.name != CANAL_OBJETIVO:
        return

    autor = reaction.message.author
    emoji_valido = "👍" if user == autor else "🔥"

    if str(reaction.emoji) != emoji_valido:
        await reaction.remove(user)
        advertencia = await reaction.message.channel.send(
            f"{user.mention} Solo se permite reaccionar con 🔥 a las publicaciones de tus compañer@s en este canal."
        )
        await advertencia.delete(delay=15)

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
