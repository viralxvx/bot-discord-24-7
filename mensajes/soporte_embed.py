import discord
from datetime import datetime

COLOR_ESTADOS = {
    "pendiente": discord.Color.orange(),
    "hecha": discord.Color.green(),
    "descartada": discord.Color.red(),
}

TEXTO_ESTADOS = {
    "pendiente": "🟠 Pendiente",
    "hecha": "✅ Hecha",
    "descartada": "❌ Descartada",
}

def generar_embed_sugerencia(data, clave):
    estado = data.get("estado", "pendiente")
    color = COLOR_ESTADOS.get(estado, discord.Color.greyple())
    estado_txt = TEXTO_ESTADOS.get(estado, "Sin estado")
    fecha_str = data.get("fecha", "¿?")
    autor = data.get("usuario", "Anónimo")
    contenido = data.get("contenido", "[Sin contenido]")

    embed = discord.Embed(
        title=f"📫 Sugerencia de {autor}",
        description=contenido,
        color=color
    )
    embed.add_field(name="Estado", value=estado_txt, inline=True)
    embed.add_field(name="Fecha", value=fecha_str, inline=True)
    embed.set_footer(text=f"ID de sugerencia: {clave}")
    return embed
