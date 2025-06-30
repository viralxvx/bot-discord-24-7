import discord
import asyncio
import datetime
from discord_bot import bot
from config import CANAL_LOGS, MAX_LOG_LENGTH, LOG_BATCH_DELAY
from state_management import save_state, faltas_dict

async def calcular_calificacion(faltas):
    porcentaje = max(0, 100 - faltas)
    barras = int(porcentaje // 10)
    barra_visual = "[" + "█" * barras + " " * (10 - barras) + "]"
    return porcentaje, f"{barra_visual} {porcentaje:.2f}%"

async def actualizar_mensaje_faltas(canal_faltas, miembro, faltas, aciertos, estado):
    try:
        calificacion, barra_visual = await calcular_calificacion(faltas)
        contenido = (
            f"👤 **Usuario**: {miembro.mention}\n"
            f"📊 **Faltas en #🧵go-viral**: {faltas} {'👻' if faltas > 0 else ''}\n"
            f"✅ **Aciertos**: {aciertos}\n"
            f"📈 **Calificación**: {barra_visual}\n"
            f"🚨 **Estado de Inactividad**: {estado}\n"
        )
        mensaje_id = faltas_dict[miembro.id]["mensaje_id"]
        if mensaje_id:
            try:
                mensaje = await canal_faltas.fetch_message(mensaje_id)
                if mensaje.content != contenido:
                    await mensaje.edit(content=contenido)
            except discord.errors.NotFound:
                mensaje = await canal_faltas.send(contenido)
                faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
        else:
            mensaje = await canal_faltas.send(contenido)
            faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
        await save_state()
    except Exception as e:
        pass

async def registrar_log(texto, categoria="general"):
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if canal_log and texto:
        try:
            if len(texto) > MAX_LOG_LENGTH:
                texto = texto[:MAX_LOG_LENGTH] + "..."
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')
            await canal_log.send(f"[{timestamp}] [{categoria.upper()}] {texto}")
        except:
            pass

async def batch_log(messages):
    canal_log = discord.utils.get(bot.get_all_channels(), name=CANAL_LOGS)
    if not canal_log:
        return
        
    for batch in messages:
        if not batch:
            continue
        combined = "\n".join(batch)
        try:
            await canal_log.send(combined)
        except:
            pass
        await asyncio.sleep(LOG_BATCH_DELAY)

async def publicar_mensaje_unico(canal, contenido, pinned=False):
    try:
        contenido_normalizado = contenido.strip().lower()
        mensajes_vistos = set()
        mensajes_a_eliminar = []
        async for msg in canal.history(limit=None):
            msg_normalizado = msg.content.strip().lower()
            if msg.author == bot.user:
                if msg_normalizado == contenido_normalizado or msg_normalizado in mensajes_vistos:
                    mensajes_a_eliminar.append(msg)
            if pinned and msg.pinned and msg.author == bot.user:
                mensajes_a_eliminar.append(msg)
        for msg in mensajes_a_eliminar:
            try:
                await msg.delete()
            except:
                pass
        mensaje = await canal.send(contenido)
        if pinned:
            await mensaje.pin()
        return mensaje
    except:
        return None
