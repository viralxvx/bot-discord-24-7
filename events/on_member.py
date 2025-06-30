import discord
from discord.ext import commands
from handlers import logs
from config import ADMIN_ID

async def on_member_join(bot: commands.Bot, member: discord.Member):
    # Puedes agregar aquí acciones al unirse un miembro, si deseas
    await logs.registrar_log(bot, f"👋 Miembro entró: {member.name}", categoria="miembros")

async def on_member_remove(bot: commands.Bot, member: discord.Member):
    await logs.registrar_log(bot, f"👋 Miembro salió: {member.name}", categoria="miembros")
