import discord
from discord.ext import tasks
import datetime
from discord_bot import bot
from config import CANAL_OBJETIVO
from state_management import (
    ultima_publicacion_dict, permisos_inactividad, 
    amonestaciones, baneos_temporales, 
    faltas_dict, save_state
)
from utils import actualizar_mensaje_faltas, registrar_log

@tasks.loop(hours=24)
async def verificar_inactividad():
    canal = discord.utils.get(bot.get_all_channels(), name=CANAL_OBJETIVO)
    if not canal:
        return
        
    canal_faltas = discord.utils.get(bot.get_all_channels(), name="📤faltas")
    ahora = datetime.datetime.now(datetime.timezone.utc)
    
    for user_id, ultima in list(ultima_publicacion_dict.items()):
        miembro = canal.guild.get_member(int(user_id))
        if not miembro or miembro.bot:
            continue
            
        permiso = permisos_inactividad.get(user_id)
        if permiso and (ahora - permiso["inicio"]).days < permiso["duracion"]:
            continue
            
        dias_inactivo = (ahora - ultima).days
        faltas = amonestaciones.get(user_id, [])
        estado = faltas_dict.get(user_id, {}).get("estado", "OK")
        aciertos = faltas_dict.get(user_id, {}).get("aciertos", 0)

        if dias_inactivo >= 3 and estado != "Baneado":
            amonestaciones[user_id] = [t for t in amonestaciones.get(user_id, []) if (ahora - t).total_seconds() < 7 * 86400]
            amonestaciones[user_id].append(ahora)
            faltas_count = len(amonestaciones[user_id])
            faltas_dict[user_id]["estado"] = "OK" if faltas_count < 3 else "Baneado"
            
            try:
                await miembro.send(
                    f"⚠️ **Falta por inactividad**: Llevas {dias_inactivo} días sin publicar\n"
                    f"📊 Faltas: {faltas_count}/3\n"
                    f"⏳ Usa `!permiso <días>` para pausar"
                )
            except:
                pass
                
            if faltas_count >= 3:
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
                await actualizar_mensaje_faltas(canal_faltas, miembro, faltas_dict[user_id]["faltas"], aciertos, "OK" if faltas_count < 3 else "Baneado")
                
        elif dias_inactivo >= 3 and estado == "Baneado" and (ahora - baneos_temporales[user_id]).days >= 3:
            faltas_dict[user_id]["estado"] = "Expulsado"
            try:
                await miembro.send(f"⛔ **Expulsado permanentemente** por inactividad")
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
