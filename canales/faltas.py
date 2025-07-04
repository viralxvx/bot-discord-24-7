import discord
from discord.ext import commands
from config import CANAL_FALTAS_ID, REDIS_URL
import redis
from datetime import datetime, timezone

# Puedes adaptar estas funciones si cambian los nombres de las claves en Redis
def obtener_estado(redis, user_id):
    estado = redis.hget(f"usuario:{user_id}", "estado")
    if not estado:
        return "Activo"
    estado = estado.lower()
    if estado == "baneado":
        return "Baneado"
    elif estado == "expulsado":
        return "Expulsado"
    elif estado == "desercion":
        return "Deserción"
    else:
        return "Activo"

def obtener_faltas(redis, user_id):
    try:
        total = int(redis.hget(f"usuario:{user_id}", "faltas_totales") or 0)
        mes = int(redis.hget(f"usuario:{user_id}", "faltas_mes") or 0)
        return total, mes
    except:
        return 0, 0

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
            # Recopilar todos los usuarios relevantes (actuales y antiguos)
            guild = canal.guild
            user_ids = set()

            # 1. Todos los miembros actuales
            for miembro in guild.members:
                if miembro.bot:
                    continue
                user_ids.add(miembro.id)

            # 2. Usuarios con estado en Redis (baneados, expulsados, deserción)
            keys = self.redis.keys("usuario:*")
            for key in keys:
                try:
                    user_id = int(key.split(":")[1])
                    user_ids.add(user_id)
                except:
                    continue

            total = 0
            for user_id in user_ids:
                miembro = guild.get_member(user_id)
                # Si ya no está, crear objeto "dummy" para mostrar su registro
                if not miembro:
                    miembro = await self.get_user_safe(guild, user_id)
                    if not miembro:
                        continue

                estado = obtener_estado(self.redis, user_id)
                faltas_total, faltas_mes = obtener_faltas(self.redis, user_id)
                embed = self.generar_embed_faltas(miembro, estado, faltas_total, faltas_mes)

                user_mention = miembro.mention
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

    async def get_user_safe(self, guild, user_id):
        try:
            user = await guild.fetch_member(user_id)
        except:
            try:
                user = await self.bot.fetch_user(user_id)
            except:
                user = None
        return user

    def generar_embed_faltas(self, miembro, estado, faltas_total, faltas_mes):
        now = datetime.now(timezone.utc)

        embed = discord.Embed(
            title=f"📤 REGISTRO DE {miembro.mention}",
            description=(
                f"**Estado actual:** {estado}\n"
                f"**Total de faltas:** {faltas_total}\n"
                f"**Faltas este mes:** {faltas_mes}"
            ),
            color=self.color_estado(estado)
        )
        embed.set_author(name=getattr(miembro, 'display_name', 'Miembro'), icon_url=getattr(miembro, 'display_avatar', discord.Embed.Empty).url if hasattr(miembro, 'display_avatar') else discord.Embed.Empty)
        embed.set_footer(text="Sistema automatizado de reputación pública", icon_url=getattr(miembro, 'display_avatar', discord.Embed.Empty).url if hasattr(miembro, 'display_avatar') else discord.Embed.Empty)
        embed.timestamp = now
        return embed

    def color_estado(self, estado):
        estado = estado.lower()
        if estado == "activo":
            return discord.Color.green()
        elif estado == "baneado":
            return discord.Color.red()
        elif estado == "expulsado":
            return discord.Color.dark_red()
        elif estado == "deserción":
            return discord.Color.orange()
        else:
            return discord.Color.greyple()

async def setup(bot):
    await bot.add_cog(Faltas(bot))
