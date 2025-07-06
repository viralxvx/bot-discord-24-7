from discord.ext import commands

class GoViral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        print("="*40)
        print(f"[DEBUG] Mensaje recibido:")
        print(f"Canal: {message.channel.id} ({message.channel.name})")
        print(f"Autor: {message.author} ({message.author.id})")
        print(f"Contenido: {message.content}")
        print("="*40)

async def setup(bot):
    await bot.add_cog(GoViral(bot))
