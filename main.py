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
                    "🔖 **Cómo Reportar Correctamente:**\n\n"
                    "1. Menciona a un usuario (ej. @Sharon) en un mensaje.\n"
                    "2. Selecciona la infracción del menú que aparecerá. \u2705\n\n"
                    "El bot registrará el reporte en 📜logs."
                )
                await fijado.pin()
            elif channel.name == CANAL_SOPORTE:
                async for msg in channel.history(limit=20):
                    if msg.author == bot.user and msg.pinned:
                        await msg.unpin()
                fijado = await channel.send(
                    "🔧 **Soporte Técnico:**\n\n"
                    "Escribe 'Hola' para abrir el menú de opciones. \u2705"
                )
                await fijado.pin()
    verificar_inactividad.start()
    clean_inactive_conversations.start()

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
        print(f"Log channel {CANAL_LOGS} not found: {texto}")

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

@tasks.loop(minutes=1)  # Verifica inactividad cada minuto
async def clean_inactive_conversations():
    canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
    if not canal_soporte:
        return
    ahora = datetime.datetime.utcnow()
    for user_id, data in list(active_conversations.items()):
        last_message_time = data.get("last_time")
        message_ids = data.get("message_ids", [])
        if last_message_time and (ahora - last_message_time).total_seconds() > INACTIVITY_TIMEOUT:
            for msg_id in message_ids:
                try:
                    msg = await canal_soporte.fetch_message(msg_id)
                    await msg.delete()
                    await registrar_log(f"Conversation cleaned for user {user_id} - Message {msg_id} deleted due to inactivity")
                except:
                    pass
            del active_conversations[user_id]

class ReportMenu(View):
    def __init__(self, reportado, autor):
        super().__init__(timeout=60)
        self.reportado = reportado
        self.autor = autor
        self.select = Select(
            placeholder="✉️ Selecciona la infracción",
            options=[
                SelectOption(label="RT", description="No hizo retweet"),
                SelectOption(label="LIKE", description="No dio like"),
                SelectOption(label="COMENTARIO", description="No comentó"),
                SelectOption(label="FORMATO", description="Formato incorrecto"),
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        razon = self.select.values[0].upper()
        ahora = datetime.datetime.utcnow()
        if self.reportado.id not in amonestaciones:
            amonestaciones[self.reportado.id] = []
        amonestaciones[self.reportado.id] = [
            t for t in amonestaciones[self.reportado.id] if (ahora - t).total_seconds() < 7 * 86400
        ]
        amonestaciones[self.reportado.id].append(ahora)
        cantidad = len(amonestaciones[self.reportado.id])
        try:
            await self.reportado.send(
                f"⚠️ Has recibido una amonestación por: **{razon}**.\n"
                f"📌 Tres amonestaciones en una semana te banean por 7 días.\n"
                f"🔀 Si reincides tras un baneo, serás expulsado definitivamente."
            )
        except:
            pass
        logs_channel = discord.utils.get(self.autor.guild.text_channels, name=CANAL_LOGS)
        if logs_channel:
            await logs_channel.send(
                f"📜 **Reporte registrado**\n"
                f"👤 Reportado: {self.reportado.mention}\n"
                f"📣 Reportado por: {self.autor.mention}\n"
                f"📌 Infracción: `{razon}`\n"
                f"📆 Amonestaciones en 7 días: `{cantidad}`"
            )
        role_baneado = discord.utils.get(self.autor.guild.roles, name="baneado")
        if cantidad >= 6 and baneos_temporales[self.reportado.id]:
            try:
                await self.reportado.send("⛔ Has sido **expulsado permanentemente** del servidor por reincidir.")
            except:
                pass
            await self.autor.guild.kick(self.reportado, reason="Expulsado por reincidencia")
            await logs_channel.send(f"❌ {self.reportado.name} fue **expulsado permanentemente** por reincidir.")
        elif quantity == 3 and not baneos_temporales[self.reportado.id]:
            if role_baneado:
                try:
                    await self.reportado.send("🚫 Has sido **baneado por 7 días** tras recibir 3 amonestaciones.")
                except:
                    pass
                await self.reportado.add_roles(role_baneado, reason="3 amonestaciones en 7 días")
                baneos_temporales[self.reportado.id] = ahora
                await logs_channel.send(f"🚫 {self.reportado.name} ha sido **baneado por 7 días**.")
        elif cantidad < 3:
            await logs_channel.send(f"ℹ️ {self.reportado.name} ha recibido una amonestación, total: {cantidad}.")
        await interaction.response.send_message("✅ Reporte registrado con éxito.", ephemeral=True)

class SupportMenu(View):
    def __init__(self, autor, query):
        super().__init__(timeout=60)
        self.autor = autor
        self.query = query
        self.select = Select(
            placeholder="🔧 Selecciona una opción",
            options=[
                SelectOption(label="Generar ticket", description="Crear un ticket para seguimiento"),
                SelectOption(label="Hablar con humano", description="Conectar con un administrador"),
                SelectOption(label="Cerrar consulta", description="Finalizar la interacción"),
                SelectOption(label="✅ ¿Cómo funciona VX?", description="Aprende cómo funciona la comunidad"),
                SelectOption(label="✅ ¿Cómo publico mi post?", description="Pasos para publicar tu contenido"),
                SelectOption(label="✅ ¿Cómo subo de nivel?", description="Cómo avanzar en la comunidad")
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        global ticket_counter, active_conversations
        user_id = self.autor.id
        await registrar_log(f"Support request from {self.autor.name} (ID: {user_id}) - Query: {self.query} - Selected: {self.select.values[0]}")
        if self.select.values[0] == "Generar ticket":
            ticket_counter += 1
            ticket_id = f"ticket-{ticket_counter:03d}"
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await registrar_log(f"Error: Admin user with ID {ADMIN_ID} not found")
                await interaction.response.send_message("❌ No pude encontrar al administrador para el ticket.", ephemeral=True)
                return
            try:
                await self.autor.send(f"🎫 Se ha generado el ticket #{ticket_id} para tu consulta: '{self.query}'. Un administrador te contactará pronto.")
                await admin.send(f"🎫 Nuevo ticket #{ticket_id} solicitado por {self.autor.mention} en #{CANAL_SOPORTE}: '{self.query}'. Por favor, responde.")
                await interaction.response.send_message(f"✅ Ticket #{ticket_id} generado. Te contactarán pronto.", ephemeral=True)
                await registrar_log(f"Ticket #{ticket_id} created for {self.autor.name}")
            except Exception as e:
                await registrar_log(f"Error generating ticket: {str(e)}")
                await interaction.response.send_message(f"❌ Error al generar el ticket: {str(e)}. Intenta de nuevo.", ephemeral=True)
        elif self.select.values[0] == "Hablar con humano":
            admin = bot.get_user(int(ADMIN_ID))
            await registrar_log(f"Attempting to notify admin with ID: {ADMIN_ID}")
            if not admin:
                await registrar_log(f"Error: Admin user with ID {ADMIN_ID} not found")
                await interaction.response.send_message("❌ No pude encontrar al administrador. Intenta de nuevo más tarde.", ephemeral=True)
                return
            try:
                await registrar_log(f"Sending DM to user {self.autor.name}")
                await self.autor.send(
                    f"🔧 Te he conectado con un administrador. Por favor, espera a que {admin.mention} te responda."
                )
                await registrar_log(f"Sending notification to admin {admin.name}")
                await admin.send(
                    f"⚠️ Nuevo soporte solicitado por {self.autor.mention} en #{CANAL_SOPORTE}: '{self.query}'. Por favor, contáctalo."
                )
                await interaction.response.send_message("✅ He notificado a un administrador. Te contactarán pronto.", ephemeral=True)
                await registrar_log(f"Support transferred successfully to {admin.name}")
            except Exception as e:
                await registrar_log(f"Error in support transfer: {str(e)}")
                await interaction.response.send_message(f"❌ Error al contactar al administrador: {str(e)}. Intenta de nuevo.", ephemeral=True)
        elif self.select.values[0] == "Cerrar consulta":
            canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
            if user_id in active_conversations and "message_ids" in active_conversations[user_id]:
                for msg_id in active_conversations[user_id]["message_ids"]:
                    try:
                        msg = await canal_soporte.fetch_message(msg_id)
                        await msg.delete()
                        await registrar_log(f"Conversation closed for user {user_id} - Message {msg_id} deleted")
                    except:
                        pass
            del active_conversations[user_id]
            await interaction.response.send_message("✅ ¡Consulta cerrada! Si necesitas más ayuda, vuelve cuando quieras. ¡Éxito con tu post y gracias por ser parte de VX! 🚀", ephemeral=True)
        elif self.select.values[0] in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
            response = faq_data.get(self.select.values[0], FAQ_FALLBACK.get(self.select.values[0], "No se encontró la respuesta."))
            msg = await interaction.response.send_message(response, ephemeral=True)
            if user_id in active_conversations:
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()

@bot.event
async def on_message(message):
    global active_conversations
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        if message.mentions:
            reportado = message.mentions[0]
            await message.channel.send(
                f"📃 Reportando a {reportado.mention}\nSelecciona la infracción que ha cometido:",
                view=ReportMenu(reportado, message.author)
            )
            await message.delete()
        else:
            await message.channel.send("⚠️ Por favor, menciona a un usuario para reportar (ej. @Sharon).")

    elif message.channel.name == CANAL_SOPORTE and not message.author.bot:
        user_id = message.author.id
        canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
        if user_id not in active_conversations:
            active_conversations[user_id] = {"message_ids": [], "last_time": datetime.datetime.utcnow()}
        if message.content.lower() in ["salir", "cancelar", "fin", "ver reglas"]:
            if message.content.lower() == "ver reglas":
                msg = await message.channel.send(MENSAJE_NORMAS)
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
            else:
                msg = await message.channel.send("✅ Consulta cerrada. ¡Vuelve si necesitas ayuda!")
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
            await message.delete()
            return

        # Mostrar menú con mensaje único
        msg = await message.channel.send("👋 Usa el menú 'Selecciona una opción' para obtener ayuda.", view=SupportMenu(message.author, message.content))
        active_conversations[user_id]["message_ids"].append(msg.id)
        active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
        await message.delete()

    elif message.channel.name == CANAL_OBJETIVO and not message.author.bot:
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
        url = urls[0].split('?')[0]
        
        # Validate the URL format
        url_pattern = r"https://x\.com/[^/]+/status/\d+"
        if not re.match(url_pattern, url):
            await message.delete()
            advertencia = await message.channel.send(
                f"{message.author.mention} el enlace no tiene el formato correcto.\nFormato: https://x.com/usuario/status/1234567890123456789"
            )
            await advertencia.delete(delay=15)
            return

        if '?' in urls[0]:
            await registrar_log(f"URL cleaned from {urls[0]} to {url} for user {message.author.name}")

        # No eliminar ni reenviar, usar el mensaje original
        new_message = message

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
            return

        ahora = datetime.datetime.utcnow()
        diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
        publicaciones_despues = [m for m in mensajes if m.created_at > ultima_publicacion.created_at and m.author != message.author]

        # Verificar que todas las publicaciones posteriores tengan reacción 🔥 del autor
        no_apoyados = []
        for msg in mensajes:
            if msg.created_at > ultima_publicacion.created_at and msg.author != message.author:
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

        if len(publicaciones_despues) < 1 and diferencia.total_seconds() < 86400:
            await new_message.delete()
            advertencia = await message.channel.send(
                f"{message.author.mention} aún no puedes publicar.\nDebes esperar al menos 24 horas desde tu última publicación si no hay otras publicaciones."
            )
            await advertencia.delete(delay=15)
            return

        def check_reaccion_propia(reaction, user):
            return reaction.message.id == new_message.id and str(reaction.emoji) == "👍" and user == message.author

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

    elif message.author == bot.user:
        return

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.channel.name != CANAL_OBJETIVO:
        return
    autor = reaction.message.author
    emoji_valido = "👍" if user == autor else "🔥"
    if str(reaction.emoji) != emoji_valido:
        await reaction.remove(user)
        advertencia = await reaction.channel.send(
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
