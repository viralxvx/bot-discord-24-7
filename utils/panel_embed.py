import discord
import json
from datetime import datetime, timezone
import os
import aiohttp
from config import CANAL_FALTAS_ID, REDIS_URL

def formatea_fecha_relativa(dt):
    if not dt:
        return "-"
    return f"<t:{int(dt.timestamp())}:R>"

def color_estado_y_emoji(estado):
    estado = estado.lower()
    if estado == "activo":
        return discord.Color.green(), "🟢"
    if estado == "baneado":
        return discord.Color.red(), "⛔"
    if estado == "expulsado":
        return discord.Color.dark_red(), "🚫"
    if estado == "prórroga":
        return discord.Color.gold(), "🟠"
    if estado == "desercion":
        return discord.Color.orange(), "⚠️"
    return discord.Color.greyple(), "⚪"

async def generar_panel_embed(redis_client, miembro):
    user_id = miembro.id
    estado = (redis_client.hget(f"usuario:{user_id}", "estado") or "Activo").capitalize()
    color, emoji_estado = color_estado_y_emoji(estado)
    faltas_total = int(redis_client.hget(f"usuario:{user_id}", "faltas_totales") or 0)
    faltas_mes = int(redis_client.hget(f"usuario:{user_id}", "faltas_mes") or 0)
    ultima_falta_ts = redis_client.hget(f"usuario:{user_id}", "ultima_falta")
    ultima_falta_dt = datetime.fromtimestamp(float(ultima_falta_ts), timezone.utc) if ultima_falta_ts else None

    # Fecha de ingreso
    fecha_ingreso = formatea_fecha_relativa(getattr(miembro, "joined_at", None))

    # Prórroga activa
    prorroga_activa = redis_client.get(f"inactividad:prorroga:{user_id}")
    prorroga_text = "—"
    if prorroga_activa:
        prorroga_dt = datetime.fromisoformat(prorroga_activa)
        pr_hist = redis_client.lrange(f"prorrogas_historial:{user_id}", -1, -1)
        motivo = ""
        if pr_hist:
            try:
                motivo = json.loads(pr_hist[0]).get("motivo", "")
            except:
                motivo = ""
        prorroga_text = f"⏳ Hasta {formatea_fecha_relativa(prorroga_dt)}"
        if motivo:
            prorroga_text += f"\n**Motivo:** {motivo}"

    # Última publicación
    last_publi = redis_client.get(f"inactividad:{user_id}")
    last_publi_dt = datetime.fromisoformat(last_publi) if last_publi else None

    # Historial reciente (últimas 3 faltas)
    faltas_hist = redis_client.lrange(f"faltas_historial:{user_id}", -3, -1)
    ultimas_faltas = []
    if faltas_hist:
        for f in faltas_hist:
            entry = json.loads(f)
            ultimas_faltas.append(
                f"`{entry['fecha']}`: {entry['motivo']} ({entry['canal']}) — {entry['moderador']}"
            )
    faltas_text = "\n".join(ultimas_faltas) if ultimas_faltas else "*Sin faltas recientes*"

    reincidencias = int(redis_client.get(f"inactividad:reincidencia:{user_id}") or 0)
    advertencias = int(redis_client.get(f"inactividad:advertencias:{user_id}") or 0)

    avatar_url = miembro.display_avatar.url if hasattr(miembro, "display_avatar") else (miembro.avatar.url if miembro.avatar else discord.Embed.Empty)

    # Tag Discord amigable (nombre#1234)
    tag = f"{miembro.name}#{miembro.discriminator}" if hasattr(miembro, "discriminator") else miembro.name

    embed = discord.Embed(
        title=f"{emoji_estado} REGISTRO DE {miembro.display_name} ({tag})",
        color=color
    )
    embed.set_thumbnail(url=avatar_url)
    embed.add_field(name="Estado actual", value=f"{emoji_estado} {estado}", inline=True)
    embed.add_field(name="Faltas totales", value=faltas_total, inline=True)
    embed.add_field(name="Faltas este mes", value=faltas_mes, inline=True)
    embed.add_field(name="Fecha de ingreso", value=fecha_ingreso, inline=True)
    if ultima_falta_dt:
        embed.add_field(name="Última falta", value=formatea_fecha_relativa(ultima_falta_dt), inline=True)
    if last_publi_dt:
        embed.add_field(name="Última publicación", value=formatea_fecha_relativa(last_publi_dt), inline=True)
    embed.add_field(name="Prórroga activa", value=prorroga_text, inline=False)
    embed.add_field(name="Advertencias activas", value=advertencias, inline=True)
    embed.add_field(name="Reincidencias inactividad", value=reincidencias, inline=True)
    embed.add_field(name="Historial reciente", value=faltas_text, inline=False)
    embed.set_footer(text="Sistema automatizado de reputación pública – Última actualización")
    embed.timestamp = datetime.now(timezone.utc)
    return embed

async def actualizar_panel_faltas(bot, miembro):
    from redis import Redis
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    user_id = miembro.id
    canal = bot.get_channel(CANAL_FALTAS_ID)
    embed = await generar_panel_embed(redis_client, miembro)

    # Guardar hash para evitar duplicados innecesarios
    panel_key = f"panel:{user_id}"
    hash_key = f"hash:{user_id}"

    # Se puede mejorar el hash, aquí solo ejemplo sencillo
    current_hash = f"{embed.title}:{embed.description}:{embed.fields}:{embed.footer.text if embed.footer else ''}"
    mensaje_id = redis_client.get(panel_key)
    previous_hash = redis_client.get(hash_key)

    webhook_url = os.getenv("WEB_HOOKS_FALTAS")
    async with aiohttp.ClientSession() as session:
        if webhook_url:
            webhook = discord.Webhook.from_url(webhook_url, session=session)
            try:
                if mensaje_id and current_hash != previous_hash:
                    await webhook.edit_message(int(mensaje_id), embed=embed)
                    redis_client.set(hash_key, current_hash)
                elif not mensaje_id:
                    msg = await webhook.send(embed=embed, wait=True)
                    redis_client.set(panel_key, msg.id)
                    redis_client.set(hash_key, current_hash)
            except Exception as e:
                print(f"❌ Error actualizando panel de {miembro.display_name}: {e}")
        else:
            # Alternativa: publicar directamente en el canal si no hay webhook
            if canal:
                if mensaje_id and current_hash != previous_hash:
                    msg = await canal.fetch_message(int(mensaje_id))
                    await msg.edit(embed=embed)
                    redis_client.set(hash_key, current_hash)
                elif not mensaje_id:
                    msg = await canal.send(embed=embed)
                    redis_client.set(panel_key, msg.id)
                    redis_client.set(hash_key, current_hash)
