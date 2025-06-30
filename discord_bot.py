import discord
from discord.ext import commands
import asyncio
from config import TOKEN, PREFIX
from events import on_ready, on_member, on_message
from tasks import clean_inactive, limpiar_expulsados, reset_faltas, verificar_inactividad
from commands import permisos

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Registrar eventos con decoradores
bot.event(on_ready.on_ready)
bot.event(on_member.on_member_join)
bot.event(on_member.on_member_remove)
bot.event(on_message.on_message)

# Registrar comandos
async def setup_commands():
    await bot.load_extension("commands.permisos")

# Evento on_ready para iniciar tareas programadas
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    # Iniciar tareas programadas
    verificar_inactividad.start()
    clean_inactive.start()
    limpiar_expulsados.start()
    reset_faltas.start()

async def main():
    await setup_commands()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
