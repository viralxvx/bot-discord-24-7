# discord_bot.py
import asyncio
from bot_instance import bot
from events import on_ready, on_member, on_message
from tasks import clean_inactive, limpiar_expulsados, reset_faltas, verificar_inactividad
from commands import permisos

# Registrar eventos
bot.event(on_ready.on_ready)
bot.event(on_member.on_member_join)
bot.event(on_member.on_member_remove)
bot.event(on_message.on_message)

# Registrar comandos - asumiendo que permisos.Permisos es un cog
async def setup_commands():
    await bot.add_cog(permisos.Permisos(bot))

# Iniciar tareas programadas cuando el bot esté listo
@bot.event
async def on_ready_event():
    verificar_inactividad.start()
    reset_faltas.start()
    clean_inactive.start()
    limpiar_expulsados.start()

bot.event(on_ready_event)

async def main():
    await setup_commands()
    await bot.start(bot.http.token)  # O usa la variable TOKEN si prefieres

if __name__ == "__main__":
    asyncio.run(main())
