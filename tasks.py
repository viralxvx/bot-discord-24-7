from discord.ext import tasks
from config import bot, CANAL_OBJETIVO, CANAL_FALTAS
from state_management import ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, faltas_dict, save_state
from utils import actualizar_mensaje_faltas, registrar_log

@tasks.loop(hours=24)
async def verificar_inactividad():
    canal = discord.utils.get(bot.get_all_channels(), name=CANAL_OBJETIVO)
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, ultima in list(ultima_publicacion_dict.items()):
        miembro = canal.guild.get_member(int(user_id))
        if not miembro or miembro.bot:
            continue
        permiso = permisos_inactividad[user_id]
        if permiso and (ahora - permiso["inicio"]).days < permiso["duracion"]:
            continue
        dias_inactivo = (ahora - ultima).days
        faltas = amonestaciones[user_id]
        estado = faltas_dict[user_id]["estado"]
        aciertos = faltas_dict[user_id]["aciertos"]

        if dias_inactivo >= 3 and estado != "Baneado":
            amonestaciones[user_id].append(ahora)
            faltas = len([t for t in amonestaciones[user_id] if (ahora - t).total_seconds() < 7 * 86400])
            faltas_dict[user_id]["estado"] = "OK" if faltas < 3 else "Baneado"
            try:
                await miembro.send(
                    f"⚠️ **Falta por inactividad**: Llevas {dias_inactivo} días sin publicar\n"
                    f"📊 Faltas: {faltas}/3\n"
                    f"⏳ Usa `!permiso <días>` para pausar"
                )
            except:
                pass
            if faltas >= 3:
                role = discord.utils.get(canal.guild.roles, name="baneado")
                if role:
                    try:
                        await miembro.add_roles(role, reason="Inactividad > 3 días")
                        baneos_temporales[user_id] = ahora
                        faltas_dict[user_id]["estado"] = "Baneado"
                        await miembro.send(
                            f"🚫 **Baneado por 7 días**: 3 faltas por inactividad\n"
                            f"📤 Publica en #🧵go-viral para levantar baneo"
                        )
                        await registrar_log(f"🚫 {miembro.name} baneado", categoria="faltas")
                    except discord.Forbidden:
                        pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "OK" if faltas < 3 else "Baneado")
        elif dias_inactivo >= 3 and estado == "Baneado" and (ahora - baneos_temporales[user_id]).days >= 3:
            faltas_dict[user_id]["estado"] = "Expulsado"
            try:
                await miembro.send(
                    f"⛔ **Expulsado permanentemente** por inactividad"
                )
            except:
                pass
            try:
                await canal.guild.kick(miembro, reason="Expulsado por reincidencia en inactividad")
                await registrar_log(f"☠️ {miembro.name} expulsado", categoria="faltas")
            except discord.Forbidden:
                pass
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "Expulsado")
        elif dias_inactivo < 3 and estado == "OK":
            amonestaciones[user_id] = []
            if canal_faltas:
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "OK")
        save_state()

@tasks.loop(hours=24)
async def resetear_faltas_diarias():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(faltas_dict.items()):
        if data["ultima_falta_time"] and (ahora - data["ultima_falta_time"]).total_seconds() >= 86400:
            miembro = discord.utils.get(bot.get_all_members(), id=int(user_id))
            if miembro:
                faltas_dict[user_id]["faltas"] = 0
                faltas_dict[user_id]["ultima_falta_time"] = None
                await actualizar_mensaje_faltas(canal_faltas, miembro, 0, data["aciertos"], data["estado"])
                try:
                    await miembro.send(
                        f"✅ **Faltas reiniciadas** en #🧵go-viral"
                    )
                except:
                    pass
    save_state()

@tasks.loop(minutes=1)
async def clean_inactive_conversations():
    canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
    if not canal_soporte:
        return
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(active_conversations.items()):
        last_message_time = data.get("last_time")
        message_ids = data.get("message_ids", [])
        if last_message_time and (ahora - last_message_time).total_seconds() > INACTIVITY_TIMEOUT:
            for msg_id in message_ids:
                try:
                    msg = await canal_soporte.fetch_message(msg_id)
                    await msg.delete()
                except:
                    pass
            del active_conversations[user_id]
    save_state()

@tasks.loop(hours=24)
async def limpiar_mensajes_expulsados():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if not canal_faltas:
        return
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(faltas_dict.items()):
        if data["estado"] == "Expulsado" and (ahora - baneos_temporales[user_id]).days >= 7:
            mensaje_id = data["mensaje_id"]
            if mensaje_id:
                try:
                    mensaje = await canal_faltas.fetch_message(mensaje_id)
                    await mensaje.delete()
                except:
                    pass
                del faltas_dict[user_id]
    save_state()
