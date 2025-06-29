from flask import Flask
from threading import Thread
import discord
import re
import os
import datetime
import json
from discord.ext import commands, tasks
from collections import defaultdict
from discord.ui import View, Select
from discord import SelectOption, Interaction

TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]
CANAL_LOGS = "📝logs"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "👨🔧soporte"
CANAL_FLUJO_SOPORTE = "flujo-de-soporte"
CANAL_ANUNCIOS = "🔔anuncios"
CANAL_NORMAS_GENERALES = "✅normas-generales"
CANAL_X_NORMAS = "𝕏-normas"
CANAL_FALTAS = "📤faltas"
ADMIN_ID = os.environ.get("ADMIN_ID", "1174775323649392844")
INACTIVITY_TIMEOUT = 300  # 5 minutos en segundos
MAX_MENSAJES_RECIENTES = 10  # Número máximo de mensajes recientes a rastrear por canal

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Estado persistente
STATE_FILE = "state.json"
try:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.fromisoformat(state.get("ultima_publicacion_dict", {}).get(str(bot.user.id), datetime.datetime.utcnow().isoformat())))
    amonestaciones = defaultdict(list, {k: [datetime.datetime.fromisoformat(t) for t in v] for k, v in state.get("amonestaciones", {}).items()})
    baneos_temporales = defaultdict(lambda: None, {k: datetime.datetime.fromisoformat(v) if v else None for k, v in state.get("baneos_temporales", {}).items()})
    permisos_inactividad = defaultdict(lambda: None, {k: {"inicio": datetime.datetime.fromisoformat(v["inicio"]), "duracion": v["duracion"]} if v else None for k, v in state.get("permisos_inactividad", {}).items()})
    ticket_counter = state.get("ticket_counter", 0)
    active_conversations = state.get("active_conversations", {})
    faq_data = state.get("faq_data", {})
    faltas_dict = defaultdict(lambda: {"faltas": 0, "aciertos": 0, "estado": "✅", "mensaje_id": None}, state.get("faltas_dict", {}))
    mensajes_recientes = defaultdict(list, state.get("mensajes_recientes", {}))
except FileNotFoundError:
    ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.utcnow())
    amonestaciones = defaultdict(list)
    baneos_temporales = defaultdict(lambda: None)
    permisos_inactividad = defaultdict(lambda: None)
    ticket_counter = 0
    active_conversations = {}
    faq_data = {}
    faltas_dict = defaultdict(lambda: {"faltas": 0, "aciertos": 0, "estado": "✅", "mensaje_id": None})
    mensajes_recientes = defaultdict(list)

def save_state():
    state = {
        "ultima_publicacion_dict": {str(k): v.isoformat() for k, v in ultima_publicacion_dict.items()},
        "amonestaciones": {str(k): [t.isoformat() for t in v] for k, v in amonestaciones.items()},
        "baneos_temporales": {str(k): v.isoformat() if v else None for k, v in baneos_temporales.items()},
        "permisos_inactividad": {str(k): {"inicio": v["inicio"].isoformat(), "duracion": v["duracion"]} if v else None for k, v in permisos_inactividad.items()},
        "ticket_counter": ticket_counter,
        "active_conversations": active_conversations,
        "faq_data": faq_data,
        "faltas_dict": {str(k): v for k, v in faltas_dict.items()},
        "mensajes_recientes": {str(k): v for k, v in mensajes_recientes.items()}
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

MENSAJE_NORMAS = (
    "📌 Bienvenid@ al canal 🧵go-viral\n\n"
    "🔹 Reacciona con 🔥 a todas las publicaciones de otros miembros desde tu última publicación antes de volver a publicar.\n"
    "🔹 Debes reaccionar a tu propia publicación con 👍.\n"
    "🔹 Solo se permiten enlaces de X (Twitter) con este formato:\n"
    "https://x.com/usuario/status/1234567890123456789\n"
    "❌ Publicaciones con texto adicional, formato incorrecto o repetidas serán eliminadas.\n"
    "⏳ **Permisos de inactividad**: Usa !permiso <días> en ⛔reporte-de-incumplimiento para pausar la obligación de publicar hasta 7 días. Extiende antes de que expire."
)

MENSAJE_ANUNCIO_PERMISOS = (
    "🚨 **NUEVA REGLA: Permisos de Inactividad**\n\n"
    "Ahora puedes solicitar un permiso de inactividad en #⛔reporte-de-incumplimiento usando el comando `!permiso <días>`:\n"
    "✅ Máximo 7 días por permiso.\n"
    "🔄 Puedes extender el permiso con otro reporte antes de que expire, siempre antes de un baneo.\n"
    "📤 Revisa tu estado en #📤faltas y mantente al día.\n"
    "¡Gracias por mantener la comunidad activa y organizada! 🚀"
)

FAQ_FALLBACK = {
    "✅ ¿Cómo funciona VX?": "VX es una comunidad donde crecemos apoyándonos. Tú apoyas, y luego te apoyan. Publicas tu post después de apoyar a los demás. 🔥 = apoyaste, 👍 = tu propio post.",
    "✅ ¿Cómo publico mi post?": "Para publicar: 1️⃣ Apoya todos los posts anteriores (like + RT + comentario) 2️⃣ Reacciona con 🔥 en Discord 3️⃣ Luego publica tu post y colócale 👍. No uses 🔥 en tu propio post ni repitas mensajes.",
    "✅ ¿Cómo subo de nivel?": "Subes de nivel participando activamente, apoyando a todos y siendo constante. Los niveles traen beneficios como prioridad, mentoría y más."
}

def calcular_calificacion(aciertos, faltas):
    total = aciertos + faltas
    if total == 0:
        return 100, "[██████████] 100%"
    porcentaje = (aciertos / total) * 100 if total > 0 else 100
    barras = int(porcentaje // 10)
    barra_visual = "[" + "█" * barras + " " * (10 - barras) + "]"
    return round(porcentaje, 2), f"{barra_visual} {porcentaje:.2f}%"

async def actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, estado):
    try:
        calificacion, barra_visual = calcular_calificacion(aciertos, faltas)
        oportunidades_restantes = 3 - faltas if estado == "👻" else (0 if estado in ["❌", "☠️"] else "Ilimitadas")
        contenido = (
            f"👤 **Usuario**: {miembro.mention}\n"
            f"📊 **Faltas**: {faltas} {'👻' if faltas > 0 else ''}\n"
            f"✅ **Aciertos**: {aciertos}\n"
            f"📈 **Calificación**: {barra_visual}\n"
            f"🚨 **Estado**: {estado}\n"
            f"⏳ **Oportunidades restantes**: {oportunidades_restantes}"
        )
        mensaje_id = faltas_dict[miembro.id]["mensaje_id"]
        if mensaje_id:
            try:
                mensaje = await canal_faltas.fetch_message(mensaje_id)
                await mensaje.edit(content=contenido)
                await registrar_log(f"📤 Mensaje actualizado para {miembro.name} en #{CANAL_FALTAS}: Faltas={faltas}, Aciertos={aciertos}, Estado={estado}", categoria="faltas")
            except discord.errors.NotFound:
                await registrar_log(f"❌ Mensaje {mensaje_id} no encontrado para {miembro.name} en #{CANAL_FALTAS}, creando uno nuevo", categoria="faltas")
                mensaje = await canal_faltas.send(contenido)
                faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
            except discord.errors.Forbidden:
                await registrar_log(f"❌ No tengo permisos para editar mensajes en #{CANAL_FALTAS} para {miembro.name}", categoria="faltas")
        else:
            mensaje = await canal_faltas.send(contenido)
            faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
            await registrar_log(f"📤 Mensaje creado para {miembro.name} en #{CANAL_FALTAS}: Faltas={faltas}, Aciertos={aciertos}, Estado={estado}", categoria="faltas")
        save_state()
    except Exception as e:
        await registrar_log(f"❌ Error al actualizar mensaje en #{CANAL_FALTAS} para {miembro.name}: {str(e)}", categoria="faltas")

async def registrar_log(texto, categoria="general"):
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if canal_log and texto:
        try:
            await canal_log.send(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] [{categoria.upper()}] {texto}")
        except discord.errors.Forbidden:
            print(f"No tengo permisos para enviar logs en #{CANAL_LOGS}: {texto}")

async def verificar_historial_repetidos():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == CANAL_LOGS:
                continue
            mensajes_vistos = set()
            mensajes_a_eliminar = []
            try:
                async for message in channel.history(limit=None):
                    if message.author == bot.user:
                        continue
                    mensaje_normalizado = message.content.strip().lower()
                    if not mensaje_normalizado:
                        continue
                    if mensaje_normalizado in mensajes_vistos:
                        mensajes_a_eliminar.append(message)
                    else:
                        mensajes_vistos.add(mensaje_normalizado)
                        canal_id = str(channel.id)
                        mensajes_recientes[canal_id].append(message.content)
                        if len(mensajes_recientes[canal_id]) > MAX_MENSAJES_RECIENTES:
                            mensajes_recientes[canal_id].pop(0)
                for message in mensajes_a_eliminar:
                    try:
                        await message.delete()
                        await registrar_log(f"🗑️ Mensaje repetido eliminado del historial en #{channel.name} por {message.author.name}: {message.content}", categoria="repetidos")
                        try:
                            await message.author.send(
                                f"⚠️ **Mensaje repetido eliminado**: Un mensaje repetido tuyo en #{channel.name} fue eliminado del historial para mantener el servidor limpio."
                            )
                        except:
                            await registrar_log(f"❌ No se pudo notificar eliminación de mensaje repetido a {message.author.name}", categoria="repetidos")
                    except discord.Forbidden:
                        await registrar_log(f"❌ No tengo permisos para eliminar mensajes en #{channel.name}", categoria="repetidos")
                save_state()
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para leer el historial en #{channel.name}", categoria="repetidos")

async def publicar_mensaje_unico(canal, contenido, pinned=False):
    try:
        contenido_normalizado = contenido.strip().lower()
        async for msg in canal.history(limit=100):
            if msg.content.strip().lower() == contenido_normalizado:
                await registrar_log(f"ℹ️ Mensaje ya existe en #{canal.name}, no se publicará de nuevo: {contenido[:50]}...", categoria="mensajes")
                return
        mensaje = await canal.send(contenido)
        if pinned:
            await mensaje.pin()
        await registrar_log(f"📢 Mensaje publicado en #{canal.name}: {contenido[:50]}...", categoria="mensajes")
    except discord.Forbidden:
        await registrar_log(f"❌ No tengo permisos para enviar/anclar mensajes en #{canal.name}", categoria="mensajes")

@bot.event
async def on_ready():
    global ticket_counter, faq_data
    print(f"Bot conectado como {bot.user}")
    await registrar_log(f"Bot iniciado. ADMIN_ID cargado: {ADMIN_ID}", categoria="bot")
    
    # Limpiar historial de mensajes repetidos
    await verificar_historial_repetidos()
    
    # Publicar mensajes en canales
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if canal_faltas:
        try:
            await publicar_mensaje_unico(canal_faltas, (
                "📢 **NUEVA ACTUALIZACIÓN DEL SISTEMA DE PARTICIPACIÓN**\n\n"
                "A partir de ahora, el sistema ha sido configurado con una nueva regla automática:\n"
                "⚠️ Si un usuario pasa **3 días sin publicar**, será **baneado por 7 días** de forma automática.\n"
                "⛔️ Si después del baneo vuelve a pasar **otros 3 días sin publicar**, el sistema procederá a **expulsarlo automáticamente** del servidor.\n"
                "✅ Esta medida busca mantener activa y comprometida a la comunidad, haciendo que el programa de crecimiento sea más eficiente y beneficioso para todos.\n"
                "📤 Revisa tu estado en este canal (#📤faltas) para mantenerte al día con tu participación.\n"
                "🚫 No repitas mensajes en ningún canal para mantener el servidor limpio.\n"
                "Gracias por su comprensión y compromiso. ¡Sigamos creciendo juntos! 🚀"
            ))
            # Inicializar mensajes para usuarios existentes
            for guild in bot.guilds:
                for member in guild.members:
                    if member.bot:
                        continue
                    if member.id not in faltas_dict:
                        faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "✅", "mensaje_id": None}
                    await actualizar_mensaje_faltas(canal_faltas, member, faltas_dict[member.id]["faltas"], faltas_dict[member.id]["aciertos"], faltas_dict[member.id]["estado"])
        except discord.Forbidden:
            await registrar_log(f"❌ No tengo permisos para enviar mensajes en #{CANAL_FALTAS}", categoria="faltas")
    else:
        await registrar_log(f"❌ Canal #{CANAL_FALTAS} no encontrado", categoria="faltas")
    
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
    if not faq_data:
        faq_data.update(FAQ_FALLBACK)
    
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == CANAL_OBJETIVO:
                async for msg in channel.history(limit=50):
                    if msg.author == bot.user:
                        await msg.delete()
                try:
                    await publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True)
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para anclar el mensaje en #{CANAL_OBJETIVO}", categoria="bot")
            elif channel.name == CANAL_REPORTES:
                async for msg in channel.history(limit=20):
                    if msg.author == bot.user and msg.pinned:
                        await msg.unpin()
                try:
                    await publicar_mensaje_unico(channel, (
                        "🔖 **Cómo Reportar Correctamente:**\n\n"
                        "1. Menciona a un usuario (ej. @Sharon) para reportar una infracción.\n"
                        "2. Selecciona la infracción del menú que aparecerá. ✅\n"
                        "3. Usa `!permiso <días>` para solicitar un permiso de inactividad (máx. 7 días).\n\n"
                        "El bot registrará el reporte en 📜logs."
                    ), pinned=True)
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para anclar el mensaje en #{CANAL_REPORTES}", categoria="bot")
            elif channel.name == CANAL_SOPORTE:
                async for msg in channel.history(limit=20):
                    if msg.author == bot.user and msg.pinned:
                        await msg.unpin()
                try:
                    await publicar_mensaje_unico(channel, (
                        "🔧 **Soporte Técnico:**\n\n"
                        "Escribe 'Hola' para abrir el menú de opciones. ✅"
                    ), pinned=True)
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para anclar el mensaje en #{CANAL_SOPORTE}", categoria="bot")
            elif channel.name == CANAL_NORMAS_GENERALES:
                async for msg in channel.history(limit=20):
                    if msg.author == bot.user and msg.pinned:
                        await msg.unpin()
                try:
                    await publicar_mensaje_unico(channel, MENSAJE_NORMAS, pinned=True)
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para anclar el mensaje en #{CANAL_NORMAS_GENERALES}", categoria="bot")
            elif channel.name == CANAL_ANUNCIOS:
                try:
                    await publicar_mensaje_unico(channel, MENSAJE_ANUNCIO_PERMISOS)
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para enviar mensajes en #{CANAL_ANUNCIOS}", categoria="bot")
    
    with open("main.py", "r") as f:
        codigo_anterior = f.read()
    await registrar_log(f"💾 Código anterior guardado:\n```python\n{codigo_anterior}\n```", categoria="bot")
    await registrar_log(f"✅ Nuevas implementaciones:\n- Logs en tiempo real para todo el servidor\n- Persistencia de estado con state.json\n- Copia de seguridad del código\n- Notificaciones en 🔔anuncios para mejoras y normas\n- Sistema de faltas en 📤faltas con contadores y calificaciones\n- Detección y eliminación de mensajes repetidos en todo el historial\n- Sistema de permisos de inactividad en ⛔reporte-de-incumplimiento", categoria="bot")
    verificar_inactividad.start()
    clean_inactive_conversations.start()
    limpiar_mensajes_expulsados.start()

@bot.event
async def on_member_join(member):
    canal_presentate = discord.utils.get(member.guild.text_channels, name="👉preséntate")
    canal_faltas = discord.utils.get(member.guild.text_channels, name=CANAL_FALTAS)
    if canal_presentate:
        try:
            mensaje = (
                f"👋 ¡Bienvenid@ a **VX** {member.mention}!\n\n"
                "Sigue estos pasos:\n"
                "📖 Lee las 3 guías\n"
                "✅ Revisa las normas\n"
                "🏆 Mira las victorias\n"
                "♟ Estudia las estrategias\n"
                "🏋 Luego solicita ayuda para tu primer post.\n\n"
                "📤 Revisa tu estado en el canal #📤faltas para mantenerte al día con tu participación.\n"
                "🚫 No repitas mensajes en ningún canal para mantener el servidor limpio.\n"
                "⏳ Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para pausar la obligación de publicar (máx. 7 días)."
            )
            await canal_presentate.send(mensaje)
        except discord.Forbidden:
            await registrar_log(f"❌ No tengo permisos para enviar mensajes en #👉preséntate", categoria="miembros")
    if canal_faltas:
        faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "✅", "mensaje_id": None}
        await actualizar_mensaje_faltas(canal_faltas, member, 0, 0, "✅")
    await registrar_log(f"👤 Nuevo miembro unido: {member.name} (ID: {member.id})", categoria="miembros")

@bot.command()
async def permiso(ctx, dias: int):
    if ctx.channel.name != CANAL_REPORTES:
        await ctx.send("⚠️ Usa este comando en #⛔reporte-de-incumplimiento.")
        return
    if dias > 7:
        await ctx.send(f"{ctx.author.mention} El máximo permitido es 7 días. Usa `!permiso <días>` con un valor entre 1 y 7.")
        await registrar_log(f"❌ Intento de permiso inválido por {ctx.author.name}: {dias} días", categoria="permisos")
        return
    if faltas_dict[ctx.author.id]["estado"] == "❌":
        await ctx.send(f"{ctx.author.mention} No puedes solicitar un permiso mientras estás baneado. Publica en #🧵go-viral para levantar el baneo.")
        await registrar_log(f"❌ Permiso denegado a {ctx.author.name}: usuario baneado", categoria="permisos")
        return
    ahora = datetime.datetime.utcnow()
    if permisos_inactividad[ctx.author.id] and (ahora - permisos_inactividad[ctx.author.id]["inicio"]).days < permisos_inactividad[ctx.author.id]["duracion"]:
        await ctx.send(f"{ctx.author.mention} Ya tienes un permiso activo hasta {permisos_inactividad[ctx.author.id]['inicio'] + datetime.timedelta(days=permisos_inactividad[ctx.author.id]['duracion'])}. Extiende antes de que expire.")
        await registrar_log(f"❌ Permiso denegado a {ctx.author.name}: permiso activo existente", categoria="permisos")
        return
    permisos_inactividad[ctx.author.id] = {"inicio": ahora, "duracion": dias}
    await ctx.send(f"✅ Permiso de inactividad otorgado a {ctx.author.mention} por {dias} días. No recibirás faltas por inactividad hasta {ahora + datetime.timedelta(days=dias)}. Extiende antes de que expire si necesitas más tiempo.")
    await registrar_log(f"✅ Permiso de inactividad otorgado a {ctx.author.name} por {dias} días", categoria="permisos")
    save_state()

@tasks.loop(hours=24)
async def verificar_inactividad():
    canal = discord.utils.get(bot.get_all_channels(), name=CANAL_OBJETIVO)
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    ahora = datetime.datetime.utcnow()
    for user_id, ultima in list(ultima_publicacion_dict.items()):
        miembro = canal.guild.get_member(int(user_id))
        if not miembro or miembro.bot:
            continue
        permiso = permisos_inactividad[user_id]
        if permiso and (ahora - permiso["inicio"]).days < permiso["duracion"]:
            continue  # Saltar usuarios con permiso activo
        dias_inactivo = (ahora - ultima).days
        faltas = faltas_dict[user_id]["faltas"]
        estado = faltas_dict[user_id]["estado"]
        aciertos = faltas_dict[user_id]["aciertos"]

        if dias_inactivo >= 3 and estado != "❌":
            faltas += 1
            faltas_dict[user_id]["faltas"] = faltas
            faltas_dict[user_id]["estado"] = "👻"
            oportunidades = 3 - faltas
            try:
                await miembro.send(
                    f"⚠️ **Falta por inactividad**: No has publicado en 🧵go-viral por {dias_inactivo} días.\n"
                    f"📊 Tienes {faltas} falta(s). Te quedan {oportunidades} oportunidades antes de un baneo de 7 días.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}.\n"
                    f"⏳ Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para pausar la obligación de publicar."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {miembro.name}", categoria="faltas")
            await registrar_log(f"⚠️ {miembro.name} recibió una falta por inactividad (Faltas: {faltas})", categoria="faltas")
            if faltas >= 3:
                role = discord.utils.get(canal.guild.roles, name="baneado")
                if role:
                    try:
                        await miembro.add_roles(role, reason="Inactividad > 3 días")
                        baneos_temporales[user_id] = ahora
                        faltas_dict[user_id]["estado"] = "❌"
                        await miembro.send(
                            f"🚫 **Baneado por 7 días**: Has acumulado 3 faltas por inactividad.\n"
                            f"📤 Revisa tu estado en #{CANAL_FALTAS}. Debes publicar dentro de los próximos 3 días para evitar expulsión."
                        )
                        await registrar_log(f"🚫 {miembro.name} baneado por 7 días por inactividad", categoria="faltas")
                    except discord.Forbidden:
                        await registrar_log(f"❌ No tengo permisos para asignar el rol baneado a {miembro.name}", categoria="faltas")
                if canal_faltas:
                    await actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, "❌")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, "👻" if faltas < 3 else "❌")
        elif dias_inactivo >= 3 and estado == "❌" and (ahora - baneos_temporales[user_id]).days >= 3:
            faltas_dict[user_id]["estado"] = "☠️"
            try:
                await miembro.send(
                    f"⛔ **Expulsado permanentemente**: No publicaste en 🧵go-viral por 3 días tras un baneo.\n"
                    f"📤 Tu estado final está en #{CANAL_FALTAS}."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar expulsión a {miembro.name}", categoria="faltas")
            try:
                await canal.guild.kick(miembro, reason="Expulsado por reincidencia en inactividad")
                await registrar_log(f"☠️ {miembro.name} expulsado por reincidencia", categoria="faltas")
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para expulsar a {miembro.name}", categoria="faltas")
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, "☠️")
        elif dias_inactivo < 3 and faltas > 0:
            if (ahora - ultima).days < 3:
                faltas_dict[user_id]["faltas"] = 0
                faltas_dict[user_id]["estado"] = "✅"
                try:
                    await miembro.send(
                        f"✅ **Contador reiniciado**: Has publicado en 🧵go-viral, tus faltas se reiniciaron a 0.\n"
                        f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                    )
                except:
                    await registrar_log(f"❌ No se pudo notificar reinicio a {miembro.name}", categoria="faltas")
                if canal_faltas:
                    await actualizar_mensaje_faltas(canal_faltas, miembro, 0, aciertos, "✅")
        save_state()

@tasks.loop(minutes=1)
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
                    await registrar_log(f"🧹 Conversación limpiada para usuario {user_id} - Mensaje {msg_id} eliminado por inactividad", categoria="soporte")
                except:
                    pass
            del active_conversations[user_id]

@tasks.loop(hours=24)
async def limpiar_mensajes_expulsados():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if not canal_faltas:
        return
    ahora = datetime.datetime.utcnow()
    for user_id, data in list(faltas_dict.items()):
        if data["estado"] == "☠️" and (ahora - baneos_temporales[user_id]).days >= 7:
            mensaje_id = data["mensaje_id"]
            if mensaje_id:
                try:
                    mensaje = await canal_faltas.fetch_message(mensaje_id)
                    await mensaje.delete()
                    await registrar_log(f"🧹 Mensaje de usuario expulsado {user_id} eliminado de #{CANAL_FALTAS}", categoria="faltas")
                except:
                    pass
                del faltas_dict[user_id]
    save_state()

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
        canal_faltas = discord.utils.get(self.autor.guild.text_channels, name=CANAL_FALTAS)
        try:
            await self.reportado.send(
                f"⚠️ Has recibido una amonestación por: **{razon}**.\n"
                f"📌 Tres amonestaciones en una semana te banean por 7 días.\n"
                f"🔀 Si reincides tras un baneo, serás expulsado definitivamente."
            )
        except:
            await registrar_log(f"❌ No se pudo notificar amonestación a {self.reportado.name}", categoria="reportes")
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
                await registrar_log(f"❌ No se pudo notificar expulsión a {self.reportado.name}", categoria="reportes")
            try:
                await self.autor.guild.kick(self.reportado, reason="Expulsado por reincidencia")
                await logs_channel.send(f"❌ {self.reportado.name} fue **expulsado permanentemente** por reincidir.")
                if canal_faltas:
                    faltas_dict[self.reportado.id]["estado"] = "☠️"
                    await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "☠️")
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para expulsar a {self.reportado.name}", categoria="reportes")
        elif cantidad >= 3 and not baneos_temporales[self.reportado.id]:
            if role_baneado:
                try:
                    await self.reportado.send("🚫 Has sido **baneado por 7 días** tras recibir 3 amonestaciones.")
                    await self.reportado.add_roles(role_baneado, reason="3 amonestaciones en 7 días")
                    baneos_temporales[self.reportado.id] = ahora
                    await logs_channel.send(f"🚫 {self.reportado.name} ha sido **baneado por 7 días**.")
                    if canal_faltas:
                        faltas_dict[self.reportado.id]["estado"] = "❌"
                        await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "❌")
                except discord.Forbidden:
                    await registrar_log(f"❌ No tengo permisos para asignar el rol baneado a {self.reportado.name}", categoria="reportes")
        elif cantidad < 3:
            await logs_channel.send(f"ℹ️ {self.reportado.name} ha recibido una amonestación, total: {cantidad}.")
        await interaction.response.send_message("✅ Reporte registrado con éxito.", ephemeral=True)
        await registrar_log(f"⚠️ Reporte realizado por {self.autor.name} contra {self.reportado.name} por {razon}", categoria="reportes")

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
        await registrar_log(f"🔧 Soporte solicitado por {self.autor.name} (ID: {user_id}) - Consulta: {self.query} - Selección: {self.select.values[0]}", categoria="soporte")
        if self.select.values[0] == "Generar ticket":
            ticket_counter += 1
            ticket_id = f"ticket-{ticket_counter:03d}"
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await registrar_log(f"❌ Error: Admin user with ID {ADMIN_ID} not found", categoria="soporte")
                await interaction.response.send_message("❌ No pude encontrar al administrador para el ticket.", ephemeral=True)
                return
            try:
                await self.autor.send(f"🎫 Se ha generado el ticket #{ticket_id} para tu consulta: '{self.query}'. Un administrador te contactará pronto.")
                await admin.send(f"🎫 Nuevo ticket #{ticket_id} solicitado por {self.autor.mention} en #{CANAL_SOPORTE}: '{self.query}'. Por favor, responde.")
                await interaction.response.send_message(f"✅ Ticket #{ticket_id} generado. Te contactarán pronto.", ephemeral=True)
                await registrar_log(f"🎫 Ticket #{ticket_id} creado para {self.autor.name}", categoria="soporte")
            except Exception as e:
                await registrar_log(f"❌ Error generando ticket: {str(e)}", categoria="soporte")
                await interaction.response.send_message(f"❌ Error al generar el ticket: {str(e)}. Intenta de nuevo.", ephemeral=True)
        elif self.select.values[0] == "Hablar con humano":
            admin = bot.get_user(int(ADMIN_ID))
            await registrar_log(f"📞 Intentando notificar al admin con ID: {ADMIN_ID}", categoria="soporte")
            if not admin:
                await registrar_log(f"❌ Error: Admin user with ID {ADMIN_ID} not found", categoria="soporte")
                await interaction.response.send_message("❌ No pude encontrar al administrador. Intenta de nuevo más tarde.", ephemeral=True)
                return
            try:
                await self.autor.send(f"🔧 Te he conectado con un administrador. Por favor, espera a que {admin.mention} te responda.")
                await admin.send(f"⚠️ Nuevo soporte solicitado por {self.autor.mention} en #{CANAL_SOPORTE}: '{self.query}'. Por favor, contáctalo.")
                await interaction.response.send_message("✅ He notificado a un administrador. Te contactarán pronto.", ephemeral=True)
                await registrar_log(f"📞 Soporte transferido exitosamente a {admin.name}", categoria="soporte")
            except Exception as e:
                await registrar_log(f"❌ Error en transferencia de soporte: {str(e)}", categoria="soporte")
                await interaction.response.send_message(f"❌ Error al contactar al administrador: {str(e)}. Intenta de nuevo.", ephemeral=True)
        elif self.select.values[0] == "Cerrar consulta":
            canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
            if user_id in active_conversations and "message_ids" in active_conversations[user_id]:
                for msg_id in active_conversations[user_id]["message_ids"]:
                    try:
                        msg = await canal_soporte.fetch_message(msg_id)
                        await msg.delete()
                        await registrar_log(f"🧹 Conversación cerrada para usuario {user_id} - Mensaje {msg_id} eliminado", categoria="soporte")
                    except:
                        pass
            del active_conversations[user_id]
            await interaction.response.send_message("✅ ¡Consulta cerrada! Si necesitas más ayuda, vuelve cuando quieras. ¡Éxito con tu post y gracias por ser parte de VX! 🚀", ephemeral=True)
        elif self.select.values[0] in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
            response = faq_data.get(self.select.values[0], FAQ_FALLBACK.get(self.select.values[0], "No se encontró la respuesta."))
            await interaction.response.send_message(response, ephemeral=True)
            if user_id in active_conversations:
                active_conversations[user_id]["message_ids"].append(interaction.message.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()

@bot.event
async def on_message(message):
    global active_conversations, mensajes_recientes
    if message.author == bot.user or message.channel.name == CANAL_LOGS:
        return
    await registrar_log(f"💬 Mensaje en #{message.channel.name} por {message.author.name} (ID: {message.author.id}): {message.content}", categoria="mensajes")
    
    # Verificar mensajes repetidos
    canal_id = str(message.channel.id)
    mensaje_normalizado = message.content.strip().lower()
    if mensaje_normalizado:
        if any(mensaje_normalizado == msg.strip().lower() for msg in mensajes_recientes[canal_id]):
            try:
                await message.delete()
                await registrar_log(f"🗑️ Mensaje repetido eliminado en #{message.channel.name} por {message.author.name}: {message.content}", categoria="repetidos")
                try:
                    await message.author.send(
                        f"⚠️ **Mensaje repetido eliminado**: No repitas mensajes en #{message.channel.name}. "
                        f"Por favor, envía contenido nuevo para mantener el servidor limpio."
                    )
                except:
                    await registrar_log(f"❌ No se pudo notificar mensaje repetido a {message.author.name}", categoria="repetidos")
                return
            except discord.Forbidden:
                await registrar_log(f"❌ No tengo permisos para eliminar mensajes en #{message.channel.name}", categoria="repetidos")
        mensajes_recientes[canal_id].append(message.content)
        if len(mensajes_recientes[canal_id]) > MAX_MENSAJES_RECIENTES:
            mensajes_recientes[canal_id].pop(0)
        save_state()

    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if message.channel.name == CANAL_REPORTES and not message.author.bot:
        if message.mentions:
            reportado = message.mentions[0]
            await message.channel.send(
                f"📃 Reportando a {reportado.mention}\nSelecciona la infracción que ha cometido:",
                view=ReportMenu(reportado, message.author)
            )
            await message.delete()
        else:
            await message.channel.send("⚠️ Por favor, menciona a un usuario para reportar (ej. @Sharon) o usa `!permiso <días>` para solicitar inactividad.")
    elif message.channel.name == CANAL_SOPORTE and not message.author.bot:
        user_id = message.author.id
        if user_id not in active_conversations:
            active_conversations[user_id] = {"message_ids": [], "last_time": datetime.datetime.utcnow()}
        if message.content.lower() in ["salir", "cancelar", "fin", "ver reglas"]:
            if message.content.lower() == "ver reglas":
                msg = await message.channel.send(MENSAJE_NORMAS)
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
                faltas_dict[user_id]["aciertos"] += 1
                if canal_faltas:
                    await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[user_id]["faltas"], faltas_dict[user_id]["aciertos"], faltas_dict[user_id]["estado"])
            else:
                msg = await message.channel.send("✅ Consulta cerrada. ¡Vuelve si necesitas ayuda!")
                active_conversations[user_id]["message_ids"].append(msg.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
            await message.delete()
            return
        msg = await message.channel.send("👋 Usa el menú 'Selecciona una opción' para obtener ayuda.", view=SupportMenu(message.author, message.content))
        active_conversations[user_id]["message_ids"].append(msg.id)
        active_conversations[user_id]["last_time"] = datetime.datetime.utcnow()
        await message.delete()
    elif message.channel.name == CANAL_OBJETIVO and not message.author.bot:
        urls = re.findall(r"https://x\.com/[^\s]+", message.content.strip())
        if len(urls) != 1 or (len(urls) == 1 and message.content.strip() != urls[0]):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["estado"] = "👻"
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], "👻")
            advertencia = await message.channel.send(
                f"{message.author.mention} solo se permite **un link válido de X** sin texto adicional.\nFormato: https://x.com/usuario/status/1234567890123456789"
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Mensaje eliminado en #{CANAL_OBJETIVO} por {message.author.name} por formato inválido", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por formato incorrecto**: Tu publicación no cumple con el formato.\n"
                    f"📊 Tienes {faltas_dict[message.author.id]['faltas']} falta(s). Te quedan {3 - faltas_dict[message.author.id]['faltas']} oportunidades antes de un baneo.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            return
        url = urls[0].split('?')[0]
        url_pattern = r"https://x\.com/[^/]+/status/\d+"
        if not re.match(url_pattern, url):
            await message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["estado"] = "👻"
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], "👻")
            advertencia = await message.channel.send(
                f"{message.author.mention} el enlace no tiene el formato correcto.\nFormato: https://x.com/usuario/status/1234567890123456789"
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Mensaje eliminado en #{CANAL_OBJETIVO} por {message.author.name} por URL inválida", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por URL inválida**: Tu enlace no tiene el formato correcto.\n"
                    f"📊 Tienes {faltas_dict[message.author.id]['faltas']} falta(s). Te quedan {3 - faltas_dict[message.author.id]['faltas']} oportunidades antes de un baneo.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            return
        if '?' in urls[0]:
            await registrar_log(f"🔧 URL limpiada de {urls[0]} a {url} para usuario {message.author.name}", categoria="publicaciones")
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
            faltas_dict[message.author.id]["aciertos"] += 1
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], "✅")
            await registrar_log(f"📅 Nueva publicación inicial de {message.author.name} en #{CANAL_OBJETIVO}", categoria="publicaciones")
            return
        ahora = datetime.datetime.utcnow()
        diferencia = ahora - ultima_publicacion.created_at.replace(tzinfo=None)
        publicaciones_despues = [m for m in mensajes if m.created_at > ultima_publicacion.created_at and m.author != message.author]
        no_apoyados = []
        for msg in mensajes:
            if msg.created_at > ultima_publicacion.created_at and msg.author != message.author:
                apoyo = False
                for reaction in msg.reactions:
                    if str(reaction.emoji) == "🔥":
                        async for user in reaction.users():
                            if user == message.author:
                                apoyo = True
                                faltas_dict[user.id]["aciertos"] += 1
                                if canal_faltas:
                                    await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], faltas_dict[user.id]["estado"])
                                break
                if not apoyo:
                    no_apoyados.append(msg)
        if no_apoyados:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["estado"] = "👻"
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], "👻")
            advertencia = await message.channel.send(
                f"{message.author.mention} debes reaccionar con 🔥 a **todas las publicaciones desde tu última publicación** antes de publicar."
            )
            await advertencia.delete(delay=15)
            urls_faltantes = [m.jump_url for m in no_apoyados]
            mensaje = (
                f"👋 {message.author.mention}, te faltan reacciones con 🔥 a los siguientes posts para poder publicar:\n" +
                "\n".join(urls_faltantes) +
                f"\n📊 Tienes {faltas_dict[message.author.id]['faltas']} falta(s). Te quedan {3 - faltas_dict[message.author.id]['faltas']} oportunidades antes de un baneo.\n"
                f"📤 Revisa tu estado en #{CANAL_FALTAS}."
            )
            await message.author.send(mensaje)
            await registrar_log(f"❌ Publicación denegada a {message.author.name} por falta de reacciones 🔥 a {len(no_apoyados)} posts", categoria="publicaciones")
            return
        if len(publicaciones_despues) < 1 and diferencia.total_seconds() < 86400:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["estado"] = "👻"
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], "👻")
            advertencia = await message.channel.send(
                f"{message.author.mention} aún no puedes publicar.\nDebes esperar al menos 24 horas desde tu última publicación si no hay otras publicaciones."
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"⏳ Publicación denegada a {message.author.name} por tiempo insuficiente (<24h)", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por tiempo insuficiente**: No has esperado 24 horas desde tu última publicación.\n"
                    f"📊 Tienes {faltas_dict[message.author.id]['faltas']} falta(s). Te quedan {3 - faltas_dict[message.author.id]['faltas']} oportunidades antes de un baneo.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            return
        def check_reaccion_propia(reaction, user):
            return reaction.message.id == new_message.id and str(reaction.emoji) == "👍" and user == message.author
        try:
            await bot.wait_for("reaction_add", timeout=60, check=check_reaccion_propia)
            faltas_dict[message.author.id]["aciertos"] += 1
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], "✅")
        except:
            await new_message.delete()
            faltas_dict[message.author.id]["faltas"] += 1
            faltas_dict[message.author.id]["estado"] = "👻"
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, message.author, faltas_dict[message.author.id]["faltas"], faltas_dict[message.author.id]["aciertos"], "👻")
            advertencia = await message.channel.send(
                f"{message.author.mention} tu publicación fue eliminada.\nDebes reaccionar con 👍 a tu propio mensaje para validarlo."
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Publicación eliminada de {message.author.name} por falta de reacción 👍", categoria="publicaciones")
            try:
                await message.author.send(
                    f"⚠️ **Falta por no reaccionar con 👍**: No reaccionaste a tu propia publicación.\n"
                    f"📊 Tienes {faltas_dict[message.author.id]['faltas']} falta(s). Te quedan {3 - faltas_dict[message.author.id]['faltas']} oportunidades antes de un baneo.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {message.author.name}", categoria="faltas")
            return
        ultima_publicacion_dict[message.author.id] = datetime.datetime.utcnow()
        await registrar_log(f"✅ Publicación validada de {message.author.name} en #{CANAL_OBJETIVO}", categoria="publicaciones")
    elif message.channel.name in [CANAL_NORMAS_GENERALES, CANAL_X_NORMAS] and not message.author.bot:
        canal_anuncios = discord.utils.get(message.guild.text_channels, name=CANAL_ANUNCIOS)
        if canal_anuncios:
            await publicar_mensaje_unico(canal_anuncios, (
                f"📢 **Actualización de Normas**: Se ha modificado una norma en #{message.channel.name}. Revisa los detalles en {message.jump_url}"
            ))
        await registrar_log(f"📝 Norma actualizada en #{message.channel.name} por {message.author.name}: {message.content}", categoria="normas")
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    await registrar_log(f"👍 Reacción añadida por {user.name} (ID: {user.id}) en #{reaction.message.channel.name}: {reaction.emoji}", categoria="reacciones")
    if user.bot or reaction.message.channel.name != CANAL_OBJETIVO:
        return
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    autor = reaction.message.author
    emoji_valido = "👍" if user == autor else "🔥"
    if reaction.message.channel.name == CANAL_OBJETIVO:
        if str(reaction.emoji) != emoji_valido:
            await reaction.remove(user)
            faltas_dict[user.id]["faltas"] += 1
            faltas_dict[user.id]["estado"] = "👻"
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], "👻")
            advertencia = await reaction.message.channel.send(
                f"{user.mention} Solo se permite reaccionar con 🔥 a las publicaciones de tus compañer@s o 👍 a tu propia publicación en este canal."
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Reacción inválida {reaction.emoji} removida de {user.name} en #{reaction.message.channel.name}", categoria="reacciones")
            try:
                await user.send(
                    f"⚠️ **Falta por reacción inválida**: Usaste un emoji incorrecto ({reaction.emoji}).\n"
                    f"📊 Tienes {faltas_dict[user.id]['faltas']} falta(s). Te quedan {3 - faltas_dict[user.id]['faltas']} oportunidades antes de un baneo.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {user.name}", categoria="faltas")
        elif str(reaction.emoji) == "🔥" and user == autor:
            await reaction.remove(user)
            faltas_dict[user.id]["faltas"] += 1
            faltas_dict[user.id]["estado"] = "👻"
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, user, faltas_dict[user.id]["faltas"], faltas_dict[user.id]["aciertos"], "👻")
            advertencia = await reaction.message.channel.send(
                f"{user.mention} No puedes reaccionar con 🔥 a tu propia publicación. Usa 👍."
            )
            await advertencia.delete(delay=15)
            await registrar_log(f"❌ Reacción 🔥 removida de {user.name} en su propia publicación en #{reaction.message.channel.name}", categoria="reacciones")
            try:
                await user.send(
                    f"⚠️ **Falta por reacción incorrecta**: No puedes usar 🔥 en tu propia publicación.\n"
                    f"📊 Tienes {faltas_dict[user.id]['faltas']} falta(s). Te quedan {3 - faltas_dict[user.id]['faltas']} oportunidades antes de un baneo.\n"
                    f"📤 Revisa tu estado en #{CANAL_FALTAS}."
                )
            except:
                await registrar_log(f"❌ No se pudo notificar falta a {user.name}", categoria="faltas")

@bot.event
async def on_member_remove(member):
    await registrar_log(f"👋 Miembro salió/expulsado: {member.name} (ID: {member.id})", categoria="miembros")

app = Flask('')

@app.route('/')
def home():
    return "El bot está corriendo!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

import atexit
atexit.register(save_state)

keep_alive()
bot.run(TOKEN)
