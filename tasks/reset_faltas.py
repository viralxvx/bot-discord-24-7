from discord.ext import tasks
import datetime
from discord_bot import bot
from config import CANAL_FALTAS
from state_management import faltas_dict, save_state
from utils import actualizar_mensaje_faltas

@tasks.loop(hours=24)
async def resetear_faltas_diarias():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if not canal_faltas:
        return
        
    ahora = datetime.datetime.now(datetime.timezone.utc)
    
    for user_id, data in list(faltas_dict.items()):
        if data["ultima_falta_time"] and (ahora - data["ultima_falta_time"]).total_seconds() >= 86400:
            miembro = discord.utils.get(bot.get_all_members(), id=int(user_id))
            if miembro:
                faltas_dict[user_id]["faltas"] = 0
                faltas_dict[user_id]["ultima_falta_time"] = None
                await actualizar_mensaje_faltas(canal_faltas, miembro, 0, data["aciertos"], data["estado"])
                try:
                    await miembro.send(f"✅ **Faltas reiniciadas** en #🧵go-viral")
                except:
                    pass
    save_state()
