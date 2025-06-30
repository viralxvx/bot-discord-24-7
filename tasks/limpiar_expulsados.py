from discord.ext import tasks
import datetime
from discord_bot import bot
from config import CANAL_FALTAS
from state_management import baneos_temporales, faltas_dict, save_state

@tasks.loop(hours=24)
async def limpiar_mensajes_expulsados():
    canal_faltas = discord.utils.get(bot.get_all_channels(), name=CANAL_FALTAS)
    if not canal_faltas:
        return
        
    ahora = datetime.datetime.now(datetime.timezone.utc)
    for user_id, data in list(faltas_dict.items()):
        if data.get("estado") == "Expulsado" and baneos_temporales.get(user_id) and (ahora - baneos_temporales[user_id]).days >= 7:
            mensaje_id = data.get("mensaje_id")
            if mensaje_id:
                try:
                    mensaje = await canal_faltas.fetch_message(mensaje_id)
                    await mensaje.delete()
                except:
                    pass
                del faltas_dict[user_id]
    save_state()
