import discord
from datetime import datetime

ESTADOS = {
    "pendiente": ("🟡 Pendiente", discord.Color.yellow()),
    "hecha": ("✅ Hecha", discord.Color.green()),
    "descartada": ("❌ Descartada", discord.Color.red())
}

def generar_embed_sugerencia(data: dict, clave: str) -> discord.Embed:
    estado = data.get("estado", "pendiente")
    estado_texto, color = ESTADOS.get(estado, ("🟡 Pendiente", discord.Color.yellow()))
    usuario = data.get("usuario", "Desconocido")
    contenido = data.get("contenido", "[Sin contenido]")
    fecha = data.get("fecha", None)

    try:
        fecha_fmt = datetime.fromisoformat(fecha).strftime('%d %b %Y • %H:%M') if fecha else "Fecha desconocida"
    except:
        fecha_fmt = "Fecha inválida"

    embed = discord.Embed(
        title=f"📬 Sugerencia de {usuario}",
        description=contenido,
        color=color
    )
    embed.set_footer(text=f"Estado: {estado_texto} | Clave: {clave}")
    embed.timestamp = datetime.utcnow()

    embed.add_field(name="🕓 Fecha enviada", value=fecha_fmt, inline=True)
    embed.add_field(name="🔖 Estado actual", value=estado_texto, inline=True)

    return embed
