import discord
from discord.ext import commands
from config import CANAL_FALTAS_ID, REDIS_URL
import redis
from datetime import datetime, timezone

class Faltas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        bot.loop.create_task(self.inicializar_panel_faltas())

    async def inicializar_panel_faltas(self):
        await self.bot.wait_until_ready()
        print("⚙️ Iniciando módulo de faltas...")

        canal = self.bot.get_channel(CANAL_FALTAS_ID)
        if not canal:
            print("❌ Error: no se encontró el canal de faltas.")
            return

        print("🔍 Cargando mensajes existentes del canal #📤faltas...")
        registros = {}

        try:
            async for mensaje in canal.history(limit=None):
                if mensaje.author.bot and mensaje.embeds:
                    embed = mensaje.embeds[0]
                    titulo = embed.title
                    if titulo and titulo.startswith("📤 REGISTRO DE "):
                        user_mention = titulo.split("📤 REGISTRO DE ")[1].strip()
                        registros[user_mention] = mensaje
        except Exception as e:
            print(f"❌ Error al leer mensajes del canal: {e}")
            return

        print("♻️ Sincronizando mensajes por miembro...")
        try:
            total = 0
            for miembro in canal.guild.members:
                if miembro.bot:
                    continue

                user_mention = miembro.mention
                embed = self.generar_embed_faltas(miembro)

                if user_mention in registros:
                    try:
                        await registros[user_mention].edit(embed=embed)
                    except Exception as e:
                        print(f"❌ Error al editar mensaje de {miembro.display_name}: {e}")
                else:
                    try:
                        await canal.send(embed=embed)
                    except Exception as e:
                        print(f"❌ Error al enviar mensaje para {miembro.display_name}: {e}")

                total += 1

            print(f"✅ Panel público actualizado. Total miembros sincronizados: {total}")

        except Exception as e:
            print(f"❌ Error al sincronizar faltas: {e}")

    def generar_embed_faltas(self, miembro):
        now = datetime.now(timezone.utc)
        timestamp = int(now.timestamp())

        embed = discord.Embed(
            title=f"📤 REGISTRO DE {miembro.mention}",
            description=(
                f"**Estado actual:** Activo\n"
                f"**Total de faltas:** 0\n"
                f"**Faltas este mes:** 0"
            ),
            color=discord.Color.orange()
        )
        embed.set_author(name=miembro.display_name, icon_url=miembro.display_avatar.url)
        embed.set_footer(text="Sistema automatizado de reputación pública", icon_url=miembro.display_avatar.url)
        embed.timestamp = now
        return embed

async def setup(bot):
    await bot.add_cog(Faltas(bot))
