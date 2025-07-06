import discord
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Responde con 'Pong!' y la latencia del bot."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latencia: {latency}ms")

    @commands.command(name="saludo")
    async def saludo(self, ctx):
        """Envía un saludo amigable."""
        await ctx.send("¡Hola! Soy VXbot, siempre listo para ayudarte.")

async def setup(bot):
    await bot.add_cog(Misc(bot))
