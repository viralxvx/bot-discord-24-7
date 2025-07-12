import discord
import redis
from config import CANAL_FALTAS_ID, REDIS_URL
from datetime import datetime, timezone

def color_estado(estado):
    estado = estado.lower()
    return {
        "activo": discord.Color.green(),
        "baneado": discord.Color.red(),
        "expulsado": discord.Color.dark_red(),
        "deserción": discord.Color.orange(),
        "prórroga": discord.Color.orange()
    }.get(estado, discord.Color.greyple())

async def actualizar_panel_faltas(bot, miembro):
    """
    Actualiza o crea el panel público de faltas para un usuario.
    Si el panel anterior fue borrado, crea uno nuevo y actualiza referencias en Redis.
    """
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    canal = bot.get_channel(CANAL_FALTAS_ID)
    if not canal:
        print(f"❌ No se encontró el canal de faltas (ID {CANAL_FALTAS_ID})")
        return

    # Datos básicos del usuario
    user_id = miembro.id
    data = redis_client.hgetall(f"usuario:{user_id}")

    estado = data.get("estado", "Activo").capitalize()
    faltas_total = int(data.get("faltas_totales", 0))
    faltas_mes = int(data.get("faltas_mes", 0))
    ultima_falta = data.get("ultima_falta")
    fecha_ultima_falta = ""
    if ultima_falta:
        try:
            fecha_ultima_falta = datetime.fromtimestamp(float(ultima_falta), timezone.utc).strftime("%d/%m/%Y %H:%M")
        except:
            fecha_ultima_falta = ""

    now = datetime.now(timezone.utc)
    avatar_url = getattr(getattr(miembro, "display_avatar", None), "url", "") or getattr(getattr(miembro, "avatar", None), "url", "")

    embed = discord.Embed(
        title=f"📤 REGISTRO DE {miembro.mention}",
        description=(
            f"**Estado actual:** {estado}\n"
            f"**Total de faltas:** {faltas_total}\n"
            f"**Faltas este mes:** {faltas_mes}\n"
            f"{f'**Última falta:** {fecha_ultima_falta}' if fecha_ultima_falta else ''}"
        ),
        color=color_estado(estado)
    )
    embed.set_author(name=getattr(miembro, 'display_name', 'Miembro'), icon_url=avatar_url)
    embed.set_footer(text="Sistema automatizado de reputación pública", icon_url=avatar_url)
    embed.timestamp = now

    # --- Gestión premium de mensaje y Redis ---
    panel_key = f"panel:{user_id}"
    hash_key = f"hash:{user_id}"
    mensaje_id = redis_client.get(panel_key)
    current_hash = f"{estado}:{faltas_total}:{faltas_mes}:{fecha_ultima_falta}"

    if redis_client.get(hash_key) == current_hash:
        # No hace falta actualizar, ya está al día
        return

    try:
        if mensaje_id:
            # Intenta editar mensaje existente
            try:
                msg = await canal.fetch_message(int(mensaje_id))
                await msg.edit(embed=embed)
            except discord.NotFound:
                # El mensaje ya no existe (404), borra referencias y crea nuevo mensaje
                redis_client.delete(panel_key)
                redis_client.delete(hash_key)
                msg = await canal.send(embed=embed)
                redis_client.set(panel_key, msg.id)
            except Exception as e:
                print(f"❌ Error actualizando panel de {miembro.display_name}: {e}")
                raise
        else:
            # No existe mensaje previo, crea uno nuevo
            msg = await canal.send(embed=embed)
            redis_client.set(panel_key, msg.id)

        # Actualiza hash (solo si no hubo error)
        redis_client.set(hash_key, current_hash)
    except Exception as e:
        print(f"❌ Error actualizando/creando panel de {miembro.display_name}: {e}")
