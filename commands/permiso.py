import discord
import datetime
from discord_bot import bot
from config import CANAL_REPORTES
from state_management import permisos_inactividad, save_state, faltas_dict
from utils import registrar_log

@bot.command()
async def permiso(ctx, dias: int):
    if ctx.channel.name != CANAL_REPORTES:
        await ctx.send("⚠️ Usa este comando en #⛔reporte-de-incumplimiento.")
        return
        
    if dias > 7:
        await ctx.send(f"{ctx.author.mention} **Máximo 7 días**")
        return
        
    if faltas_dict[ctx.author.id]["estado"] == "Baneado":
        await ctx.send(f"{ctx.author.mention} **No puedes solicitar permiso baneado**")
        return
        
    ahora = datetime.datetime.now(datetime.timezone.utc)
    if permisos_inactividad[ctx.author.id] and (ahora - permisos_inactividad[ctx.author.id]["inicio"]).days < permisos_inactividad[ctx.author.id]["duracion"]:
        await ctx.send(f"{ctx.author.mention} **Ya tienes permiso activo**")
        return
        
    permisos_inactividad[ctx.author.id] = {"inicio": ahora, "duracion": dias}
    await ctx.send(f"✅ **Permiso otorgado** a {ctx.author.mention} por {dias} días")
    await registrar_log(f"Permiso: {ctx.author.name} por {dias}d", categoria="permisos")
    save_state()
