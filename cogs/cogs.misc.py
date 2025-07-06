from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.lower() == "hola bot":
            await message.channel.send("👋 ¡Hola, soy VXbot y estoy vivo!")
        # OJO: NO llames a bot.process_commands aquí, el bot ya lo hace solo

async def setup(bot):
    await bot.add_cog(Misc(bot))
