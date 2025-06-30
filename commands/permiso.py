import datetime
from discord.ext import commands
from utils import registrar_log, save_state
from redis_database import load_state, save_state as redis_save_state

CANAL_REPORTES = "⛔reporte-de-incumplimiento"

class Permisos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.permisos_inactividad = load_state("permisos_inactividad", {})

    @commands.command()
    async def permiso(self, ctx, dias: int):
        if ctx.channel.name != CANAL_REPORTES:
            await ctx.send("⚠️ Usa este comando en #⛔reporte-de-incumplimiento.")
            return
        if dias > 7:
            await ctx.send(f"{ctx.author.mention} **Máximo 7 días**")
            return
        estado = self.permisos_inactividad.get(ctx.author.id, {}).get("estado", None)
        if estado == "Baneado":
            await ctx.send(f"{ctx.author.mention} **No puedes solicitar permiso baneado**")
            return

        ahora = datetime.datetime.now(datetime.timezone.utc)
        permiso = self.permisos_inactividad.get(ctx.author.id)
        if permiso and (ahora - permiso["inicio"]).days < permiso["duracion"]:
            await ctx.send(f"{ctx.author.mention} **Ya tienes permiso activo**")
            return

        self.permisos_inactividad[ctx.author.id] = {"inicio": ahora, "duracion": dias}
        redis_save_state("permisos_inactividad", self.permisos_inactividad)

        await ctx.send(f"✅ **Permiso otorgado** a {ctx.author.mention} por {dias} días")
        await registrar_log(self.bot, f"Permiso: {ctx.author.name} por {dias}d", categoria="permisos")

async def setup(bot):
    await bot.add_cog(Permisos(bot))
