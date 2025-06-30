from discord.ext import tasks
import discord
import datetime
from discord_bot import bot
from config import CANAL_OBJETIVO
from state_management import (
    ultima_publicacion_dict, permisos_inactividad, 
    amonestaciones, baneos_temporales, 
    faltas_dict, save_state
)
from utils import actualizar_mensaje_faltas, registrar_log
from handlers.faltas import actualizar_estado_usuario

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
            
        permiso = permisos_inactividad[user_id]
        if permiso and (ahora - permiso["inicio"]).days < permiso["duracion"]:
            continue
            
        dias_inactivo = (ahora - ultima).days
        await actualizar_estado_usuario(user_id, dias_inactivo)
                
    save_state()
