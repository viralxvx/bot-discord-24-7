# utils/formatter.py

import discord
from datetime import datetime

# Colores por categoría
COLOR_CATEGORIAS = {
    "monetizacion": 0xFFD700,     # Dorado
    "viralidad": 0x1DA1F2,        # Azul Twitter
    "mentalidad": 0x00C897,       # Verde menta
    "progreso": 0xB084EB          # Violeta claro
}

def generar_estrellas(calificacion: int) -> str:
    return "⭐️" * calificacion + "☆" * (5 - calificacion)

def formatear_fecha():
    fecha = datetime.now()
    return fecha.strftime("%d %b %Y · %H:%M")

def crear_embed_testimonio(usuario, contenido, tipo, tiempo, impacto, calificacion, destacar="", anonimo=False):
    nombre = "Anónimo" if anonimo else f"@{usuario.display_name}"
    avatar = None if anonimo else usuario.display_avatar

    estrellas = generar_estrellas(calificacion)
    color = COLOR_CATEGORIAS.get(tipo, 0x2F3136)

    embed = discord.Embed(
        title=f"📤 TESTIMONIO DE {nombre}",
        description=f"{estrellas}\n\n*\"{contenido}\"*",
        color=color
    )

    embed.add_field(name="🕒 Tiempo en lograr resultados", value=tiempo, inline=True)
    embed.add_field(name="🚀 Impacto logrado", value=impacto, inline=True)

    if destacar:
        embed.add_field(name="💡 Lo que más le gustó", value=destacar, inline=False)

    embed.set_footer(text=f"Calificación: {calificacion}/5 · Sistema VX · {formatear_fecha()}")

    if avatar:
        embed.set_thumbnail(url=avatar.url)

    return embed
