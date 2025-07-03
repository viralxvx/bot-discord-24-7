import discord
from discord.ext import commands
from config import CANAL_SOPORTE_ID, REDIS_URL
import redis
from datetime import datetime, timedelta, timezone
from mensajes.inactividad_texto import PRORROGA_CONCEDIDA

class SoporteProrroga(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id != CANAL_SOPORTE_ID:
            return
        member = message.author
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return

        key_prorroga = f"inactividad:prorroga:{member.id}"
        prorroga_actual = self.redis.get(key_prorroga)
        ahora = datetime.now(timezone.utc)
        if prorroga_actual:
            fecha_prorroga = datetime.fromisoformat(prorroga_actual)
            if ahora < fecha_prorroga:
                await message.reply(
                    "⏳ Ya tienes una prórroga activa. Espera a que termine antes de solicitar otra.",
                    mention_author=False
                )
                return

        dias = 7
        hasta = ahora + timedelta(days=dias)
        self.redis.set(key_prorroga, hasta.isoformat())
        print(f"⏳ [PRÓRROGA] Prórroga CONCEDIDA a {member.display_name} ({member.id}) hasta {hasta.isoformat()} [solicitada en soporte]")

        try:
            await message.delete()
        except Exception:
            pass

        try:
            await member.send(PRORROGA_CONCEDIDA.format(dias=dias))
        except Exception as e:
            print(f"⚠️ [PRÓRROGA] No se pudo enviar DM a {member.display_name}: {e}")

        try:
            aviso = await message.channel.send(
                f"✅ {member.mention}, tu prórroga de {dias} días fue registrada. Revisa tu DM.",
                delete_after=10
            )
        except Exception:
            pass

# ¡AQUÍ EL CAMBIO CLAVE!
async def setup(bot):
    await bot.add_cog(SoporteProrroga(bot))
