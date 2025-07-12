import discord
from discord.ext import commands
from config import CANAL_FALTAS_ID, REDIS_URL
from utils.panel_embed import actualizar_panel_faltas
import redis

class MigrarPaneles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @commands.command(name="migrar_paneles", help="Migra todos los paneles viejos de faltas al formato premium (solo admin).")
    @commands.has_permissions(administrator=True)
    async def migrar_paneles(self, ctx):
        canal = self.bot.get_channel(CANAL_FALTAS_ID)
        if not canal:
            await ctx.send("❌ No se encontró el canal de faltas.")
            return

        await ctx.send("🔄 Migrando paneles viejos al nuevo formato premium. Esto puede tardar unos minutos...")

        guild = ctx.guild
        migrados = 0
        for member in guild.members:
            if member.bot:
                continue
            try:
                await actualizar_panel_faltas(self.bot, member)
                migrados += 1
            except Exception as e:
                print(f"❌ Error migrando panel de {member.display_name}: {e}")

        await ctx.send(f"✅ Paneles migrados: {migrados}. ¡Todos los mensajes están ahora en el nuevo formato premium!")

async def setup(bot):
    await bot.add_cog(MigrarPaneles(bot))
