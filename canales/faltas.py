import discord
from discord.ext import commands, tasks
from config import CANAL_FALTAS_ID, REDIS_URL
import redis.asyncio as redis
import datetime

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.mensajes_panel = {}  # user_id: message_id

    @commands.Cog.listener()
    async def on_ready(self):
        print("\n⚙️ Iniciando módulo de faltas...")
        canal = self.bot.get_channel(CANAL_FALTAS_ID)
        if not canal:
            print(f"❌ No se encontró el canal con ID {CANAL_FALTAS_ID}")
            return

        await self.limpiar_canal(canal)
        await self.reconstruir_panel_publico(canal)

    async def limpiar_canal(self, canal):
        print("🧹 Borrando todos los mensajes del canal #📤faltas...")
        try:
            async for mensaje in canal.history(limit=None):
                await mensaje.delete()
            print("✅ Canal limpiado con éxito.")
        except Exception as e:
            print(f"❌ Error al limpiar el canal: {e}")

    async def reconstruir_panel_publico(self, canal):
        print("📊 Reconstruyendo panel público de faltas...")
        keys = await self.redis.keys("faltas:*")
        usuarios = set(k.split(":")[1] for k in keys if k.count(":") == 1)

        for user_id in usuarios:
            miembro = canal.guild.get_member(int(user_id))
            if not miembro:
                continue
            await self.publicar_o_actualizar_usuario(canal, miembro)
        print("✅ Panel público actualizado.")

    async def publicar_o_actualizar_usuario(self, canal, miembro):
        user_id = str(miembro.id)
        total_faltas = await self.redis.get(f"faltas:{user_id}") or 0
        mes_actual = datetime.datetime.utcnow().strftime("%Y-%m")
        faltas_mes = await self.redis.get(f"faltas:{user_id}:{mes_actual}") or 0
        estado = await self.redis.get(f"estado:{user_id}") or "Activo"
        timestamp = await self.redis.get(f"ultimo_registro:{user_id}")

        embed = discord.Embed(
            title=f"📤 REGISTRO DE {miembro.display_name}",
            description=f"**Estado actual:** `{estado}`\n**Total de faltas:** `{total_faltas}`\n**Faltas este mes:** `{faltas_mes}`",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        if timestamp:
            fecha = datetime.datetime.fromtimestamp(int(timestamp))
            embed.add_field(name="🕓 Última falta", value=f"<t:{int(fecha.timestamp())}:R>", inline=False)

        embed.set_footer(text="Sistema automatizado de reputación pública")
        embed.set_author(name=miembro.display_name, icon_url=miembro.display_avatar.url)

        try:
            mensaje = await canal.send(embed=embed)
            self.mensajes_panel[user_id] = mensaje.id
        except Exception as e:
            print(f"❌ Error al publicar registro público para {miembro.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(Faltas(bot))
