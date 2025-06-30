import discord
from discord.ext import commands
import datetime

class Permisos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="permiso")
    async def permiso(self, ctx, dias: int = 1):
        """Solicita permiso por una cantidad de días (por defecto 1 día)."""
        if dias < 1 or dias > 30:
            await ctx.send("❌ Por favor, ingresa un número de días válido entre 1 y 30.")
            return
        
        # Aquí puedes agregar lógica para registrar el permiso en base de datos o notificar admins
        fecha_fin = datetime.datetime.utcnow() + datetime.timedelta(days=dias)
        
        await ctx.send(
            f"✅ {ctx.author.mention} has solicitado permiso por {dias} día(s), válido hasta {fecha_fin.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )
        
        # Ejemplo de notificación a canal de logs o admin (ajusta según tu bot)
        canal_logs = discord.utils.get(ctx.guild.text_channels, name="logs")
        if canal_logs:
            await canal_logs.send(
                f"📢 Permiso solicitado por {ctx.author.mention} por {dias} día(s)."
            )

async def setup(bot):
    await bot.add_cog(Permisos(bot))
