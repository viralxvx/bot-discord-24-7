import discord

def generar_embed_estado(usuario, info):
    embed = discord.Embed(
        title="📌 Estado del Usuario",
        description=f"Consulta personalizada para {usuario.mention}",
        color=discord.Color.orange()
    )

    embed.add_field(name="🆔 Usuario", value=f"{usuario.name}#{usuario.discriminator}", inline=False)
    embed.add_field(name="📊 Faltas acumuladas", value=f"{info.get('faltas', 0)}", inline=True)
    embed.add_field(name="🗓️ Estado actual", value=f"{info.get('estado', 'Desconocido')}", inline=True)

    if info.get("estado") == "Baneado":
        embed.set_footer(text="⛔ Actualmente estás baneado. Contacta soporte si es un error.")
    elif info.get("estado") == "Expulsado":
        embed.set_footer(text="🚫 Usuario expulsado del servidor.")
    else:
        embed.set_footer(text="✅ Estado activo. ¡Sigue participando y creciendo!")

    return embed

def generar_embed_estadisticas(total, baneados, expulsados):
    embed = discord.Embed(
        title="📈 Estadísticas Generales de la Comunidad",
        description="Panel informativo para administradores",
        color=discord.Color.green()
    )

    embed.add_field(name="👥 Total de miembros", value=str(total), inline=True)
    embed.add_field(name="⛔ Miembros baneados", value=str(baneados), inline=True)
    embed.add_field(name="🚫 Miembros expulsados", value=str(expulsados), inline=True)

    embed.set_footer(text="Solo visible para administradores con acceso al canal 💻comandos.")
    return embed
