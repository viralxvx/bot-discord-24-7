import discord
from discord.ext import commands
from config import CANAL_FALTAS_ID, ADMIN_ID, REDIS_URL
import redis.asyncio as redis
import datetime

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)

    @commands.Cog.listener()
    async def on_ready(self):
        print("⚙️ Módulo de faltas activo.")

    async def registrar_falta(self, user: discord.Member, motivo: str):
        user_id = str(user.id)
        key = f"faltas:{user_id}"

        # Incrementar contador en Redis
        faltas_actuales = await self.redis.incr(key)
        await self.redis.expire(key, 60 * 60 * 24 * 365 * 10)  # 10 años

        # Enviar DM elegante
        try:
            embed_dm = discord.Embed(
                title="⚠️ Has recibido una falta en Viral 𝕏 | V𝕏",
                description=(
                    f"**Motivo:** {motivo}\n"
                    f"**Cantidad actual de faltas:** {faltas_actuales}\n\n"
                    "Por favor, repasa las normas del canal 🧵go-viral en **#✅normas-generales** para evitar futuras sanciones.\n\n"
                    "Recuerda: este sistema está automatizado, y busca educar, no castigar.\n\n"
                    "Estamos aquí para ayudarte a crecer. 🚀"
                ),
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            embed_dm.set_footer(text="Sistema automatizado de faltas")

            await user.send(embed=embed_dm)
            print(f"📬 Falta enviada por DM a {user.display_name}")
        except Exception as e:
            print(f"❌ No se pudo enviar DM a {user.display_name}: {e}")

        # Publicar en canal #📤faltas
        canal_faltas = self.bot.get_channel(CANAL_FALTAS_ID)
        if canal_faltas:
            embed_publico = discord.Embed(
                title="📤 NUEVA FALTA REGISTRADA",
                description=(
                    f"**Usuario:** {user.mention} (`{user.display_name}`)\n"
                    f"**Motivo:** {motivo}\n"
                    f"**Total de faltas:** {faltas_actuales}\n"
                    f"**Fecha:** <t:{int(datetime.datetime.utcnow().timestamp())}:f>"
                ),
                color=discord.Color.dark_red()
            )
            embed_publico.set_footer(text="Sistema automatizado de faltas")
            try:
                await canal_faltas.send(embed=embed_publico)
                print(f"✅ Falta publicada en canal de faltas")
            except Exception as e:
                print(f"❌ No se pudo publicar en #📤faltas: {e}")

    async def contar_faltas(self, user: discord.Member) -> int:
        key = f"faltas:{user.id}"
        value = await self.redis.get(key)
        return int(value) if value else 0

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_FALTAS_ID and not message.author.bot:
            try:
                await message.delete()
                print(f"🗑️ Mensaje de {message.author} eliminado en #📤faltas")
            except Exception as e:
                print(f"❌ No se pudo borrar mensaje en faltas: {e}")

async def setup(bot):
    await bot.add_cog(Faltas(bot))
