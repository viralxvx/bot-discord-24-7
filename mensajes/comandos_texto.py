import discord

def generar_embed_estado(usuario, data_usuario):
    embed = discord.Embed(
        title="📊 Estado del Usuario",
        description=f"**Usuario:** {usuario.mention}\n**Estado:** {data_usuario.get('estado', 'Activo')}",
        color=discord.Color.blue()
    )
    embed.add_field(name="📅 Faltas del mes", value=str(data_usuario.get('faltas_mes', 0)), inline=True)
    embed.add_field(name="❌ Faltas totales", value=str(data_usuario.get('faltas_totales', 0)), inline=True)
    
    estado = str(data_usuario.get("estado", "")).lower()
    if estado in ["baneado", "expulsado"]:
        embed.set_footer(text="Este usuario ha sido sancionado.")
    elif int(data_usuario.get("faltas_totales", 0)) >= 3:
        embed.set_footer(text="⚠️ Está en riesgo de ser baneado.")
    else:
        embed.set_footer(text="Todo en orden.")

    return embed

def generar_embed_estadisticas(
    total_miembros,
    total_baneados,
    total_expulsados,
    total_deserciones,
    total_activos
):
    embed = discord.Embed(
        title="📈 Estadísticas Generales del Servidor",
        color=discord.Color.green()
    )
    embed.add_field(name="👥 Miembros totales", value=str(total_miembros), inline=True)
    embed.add_field(name="🟢 Activos", value=str(total_activos), inline=True)
    embed.add_field(name="⛔ Baneados", value=str(total_baneados), inline=True)
    embed.add_field(name="🚫 Expulsados", value=str(total_expulsados), inline=True)
    embed.add_field(name="🚪 Deserciones", value=str(total_deserciones), inline=True)
    embed.set_footer(text="Panel actualizado por el bot.")
    return embed

INSTRUCCIONES_COMANDOS = """
🎯 **COMANDOS DISPONIBLES**

`/estado` – Consulta tu situación actual en el sistema: número de faltas, estado (activo, baneado o expulsado), y si estás en riesgo de sanción.

`/estadisticas` – (Solo administradores) Muestra estadísticas generales: cantidad de miembros, expulsados y baneados.

🕐 **IMPORTANTE:** Las respuestas serán visibles por 10 minutos y luego se eliminarán automáticamente del canal.

📬 También recibirás una copia por mensaje directo como constancia.

⚠️ **Este canal es exclusivo para comandos.**
"""
