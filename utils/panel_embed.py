import discord
import redis
from config import CANAL_FALTAS_ID, REDIS_URL, CANAL_OBJETIVO_ID
from datetime import datetime, timezone, timedelta

def color_estado(estado):
    estado = estado.lower()
    return {
        "activo": discord.Color.green(),
        "baneado": discord.Color.red(),
        "expulsado": discord.Color.dark_red(),
        "deserción": discord.Color.orange(),
        "prórroga": discord.Color.orange(),
        "advertido": discord.Color.gold()
    }.get(estado, discord.Color.greyple())

def tiempo_relativo(dt):
    """Convierte una fecha a formato 'hace X horas/días'."""
    if not dt:
        return "-"
    now = datetime.now(timezone.utc)
    diff = now - dt
    if diff.days >= 1:
        return f"hace {diff.days} días"
    horas = int(diff.total_seconds() // 3600)
    if horas >= 1:
        return f"hace {horas} horas"
    minutos = int(diff.total_seconds() // 60)
    return f"hace {minutos} min"

async def actualizar_panel_faltas(bot, miembro):
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    canal = bot.get_channel(CANAL_FALTAS_ID)
    if not canal:
        print(f"❌ No se encontró el canal de faltas (ID {CANAL_FALTAS_ID})")
        return

    user_id = miembro.id
    data = redis_client.hgetall(f"usuario:{user_id}")

    estado = data.get("estado", "Activo").capitalize()
    faltas_total = int(data.get("faltas_totales", 0))
    faltas_mes = int(data.get("faltas_mes", 0))

    # Última falta
    ultima_falta_ts = data.get("ultima_falta")
    if ultima_falta_ts:
        ultima_falta_dt = datetime.fromtimestamp(float(ultima_falta_ts), timezone.utc)
        ultima_falta_str = tiempo_relativo(ultima_falta_dt)
    else:
        ultima_falta_dt = None
        ultima_falta_str = "-"

    # Última publicación en canal objetivo
    key_last_post = f"inactividad:{user_id}"
    last_post_iso = redis_client.get(key_last_post)
    if last_post_iso:
        last_post_dt = datetime.fromisoformat(last_post_iso)
        last_post_str = tiempo_relativo(last_post_dt)
    else:
        last_post_str = "-"

    # Prórroga activa
    key_prorroga = f"inactividad:prorroga:{user_id}"
    prorroga_iso = redis_client.get(key_prorroga)
    prorroga_str = "-"
    if prorroga_iso:
        prorroga_dt = datetime.fromisoformat(prorroga_iso)
        if prorroga_dt > datetime.now(timezone.utc):
            diff = prorroga_dt - datetime.now(timezone.utc)
            prorroga_str = f"Hasta en {diff.days} días"
        else:
            prorroga_str = "-"

    # Historial reciente de faltas (últimas 3)
    key_historial = f"historial_faltas:{user_id}"
    historial = redis_client.lrange(key_historial, 0, 2)
    historial_str = ""
    if historial:
        for entry in historial:
            # entry puede ser un JSON string con fecha/motivo
            try:
                import json
                data_falta = json.loads(entry)
                fecha = data_falta.get("fecha", "")
                motivo = data_falta.get("motivo", "")
                canal = data_falta.get("canal", "")
                staff = data_falta.get("staff", "")
                fecha_obj = datetime.fromisoformat(fecha) if fecha else None
                rel = tiempo_relativo(fecha_obj) if fecha_obj else fecha
                historial_str += f"• {rel}: {motivo} {f'({canal})' if canal else ''} {f'— {staff}' if staff else ''}\n"
            except Exception:
                historial_str += f"• {entry}\n"
    else:
        historial_str = "Sin faltas recientes"

    # Reincidencias
    reincidencias = int(redis_client.get(f"inactividad:reincidencia:{user_id}") or 0)

    # Fecha de ingreso (opcional, solo si lo guardas)
    # fecha_ingreso = data.get("fecha_ingreso")  # ISO
    # fecha_ingreso_str = fecha_ingreso if fecha_ingreso else "-"

    now = datetime.now(timezone.utc)
    avatar_url = getattr(getattr(miembro, "display_avatar", None), "url", "") or getattr(getattr(miembro, "avatar", None), "url", "")

    embed = discord.Embed(
        title=f"📤 REGISTRO DE {miembro.display_name} ({miembro.name})",
        color=color_estado(estado),
        timestamp=now
    )
    embed.set_author(name=miembro, icon_url=avatar_url)
    embed.add_field(name="Estado actual", value=estado, inline=True)
    embed.add_field(name="Faltas totales", value=str(faltas_total), inline=True)
    embed.add_field(name="Faltas este mes", value=str(faltas_mes), inline=True)
    embed.add_field(name="Última falta", value=ultima_falta_str, inline=True)
    embed.add_field(name="Última publicación", value=last_post_str, inline=True)
    embed.add_field(name="Prórroga activa", value=prorroga_str, inline=True)
    embed.add_field(name="Historial reciente", value=historial_str or "-", inline=False)
    embed.add_field(name="Reincidencias", value=str(reincidencias), inline=True)
    embed.set_footer(text="Sistema automatizado de reputación pública", icon_url=avatar_url)

    # Panel management (robusto, premium)
    panel_key = f"panel:{user_id}"
    hash_key = f"hash:{user_id}"
    mensaje_id = redis_client.get(panel_key)
    current_hash = f"{estado}:{faltas_total}:{faltas_mes}:{ultima_falta_str}:{last_post_str}:{prorroga_str}:{historial_str}"

    if redis_client.get(hash_key) == current_hash:
        return  # Panel ya actualizado, no repite

    try:
        if mensaje_id:
            try:
                msg = await canal.fetch_message(int(mensaje_id))
                await msg.edit(embed=embed)
            except discord.NotFound:
                redis_client.delete(panel_key)
                redis_client.delete(hash_key)
                msg = await canal.send(embed=embed)
                redis_client.set(panel_key, msg.id)
            except Exception as e:
                print(f"❌ Error actualizando panel de {miembro.display_name}: {e}")
                raise
        else:
            msg = await canal.send(embed=embed)
            redis_client.set(panel_key, msg.id)

        redis_client.set(hash_key, current_hash)
    except Exception as e:
        print(f"❌ Error actualizando/creando panel de {miembro.display_name}: {e}")
