import discord

def generar_embed_estado(user, data):
    estado = data.get("estado", "activo").capitalize()
    total_faltas = data.get("total", "0")
    mes_faltas = data.get("mes", "0")

    embed = discord.Embed(
        title="📊 Tu Estado Actual",
        description=f"Consulta actualizada de tu situación en el sistema.",
        color=discord.Color.orange()
    )

    embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    embed.add_field(name="Estado", value=estado, inline=True)
    embed.add_field(name="Faltas este mes", value=mes_faltas, inline=True)
    embed.add_field(name="Faltas totales", value=total_faltas, inline=True)

    if estado.lower() == "baneado":
        embed.set_footer(text="Estás temporalmente bloqueado. Consulta con el bot para más detalles.")
    elif estado.lower() == "expulsado":
        embed.set_footer(text="Has sido expulsado permanentemente del sistema.")
    else:
        embed.set_footer(text="Sigue participando y evita sanciones.")

    return embed

def generar_embed_estadisticas(total, baneados, expulsados):
    embed = discord.Embed(
        title="📈 Estadísticas del Sistema",
        description="Resumen general del estado actual de la comunidad.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Miembros registrados", value=str(total), inline=False)
    embed.add_field(name="Baneados", value=str(baneados), inline=True)
    embed.add_field(name="Expulsados", value=str(expulsados), inline=True)

    embed.set_footer(text="Actualizado automáticamente por el sistema.")
    return embed
