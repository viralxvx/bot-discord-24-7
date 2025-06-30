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
            except discord.NotFound:
                # El mensaje fue eliminado, crear uno nuevo
                mensaje = await canal_faltas.send(contenido)
                faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
            except discord.Forbidden:
                pass
        else:
            mensaje = await canal_faltas.send(contenido)
            faltas_dict[miembro.id]["mensaje_id"] = mensaje.id
        save_state()
    except Exception as e:
        print(f"Error actualizando mensaje faltas: {str(e)}")
