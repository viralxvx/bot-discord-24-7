from discord.ext import commands, tasks
from .config import intents, bot
from .state_management import load_state, save_state
from .utils import registrar_log

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    load_state()
    
    if not verificar_inactividad.is_running():
        verificar_inactividad.start()
    if not clean_inactive_conversations.is_running():
        clean_inactive_conversations.start()
    if not limpiar_mensajes_expulsados.is_running():
        limpiar_mensajes_expulsados.start()
    if not resetear_faltas_diarias.is_running():
        resetear_faltas_diarias.start()
    
    log_text = ["Bot iniciado"]
    await registrar_log("\n".join(log_text))

@bot.event
async def on_member_remove(member):
    await registrar_log(f"👋 Miembro salió: {member.name}", categoria="miembros")
    save_state(log=True)
