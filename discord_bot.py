import discord
from discord.ext import commands
import asyncio
from config import TOKEN, PREFIX
from events import on_ready, on_member, on_message
from tasks import clean_inactive, limpiar_expulsados, reset_faltas, verificar_inactividad

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Registrar eventos
bot.event(on_ready.on_ready)
bot.event(on_member.on_member_join)
bot.event(on_member.on_member_remove)
bot.event(on_message.on_message)

# Iniciar tareas programadas cuando el bot esté listo
@bot.event
async def on_ready_event():
    verificar_inactividad.start()
    reset_faltas.start()
    clean_inactive.start()
    limpiar_expulsados.start()

bot.event(on_ready_event)

async def main():
    # Cargar extensiones (cogs)
    await bot.load_extension("commands.permisos")

    # Ejecutar bot
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
