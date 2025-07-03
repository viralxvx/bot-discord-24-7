import discord
from discord.ext import commands
import os
import asyncio
from config import CANAL_FALTAS_ID, REDIS_URL
import redis
from datetime import datetime
import pytz

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
        mensajes_existentes = [m async for m in canal.history(limit=None)]
        mensajes_por_usuario = {}

        for mensaje in mensajes_existentes:
            if mensaje.author != self.bot.user or not mensaje.embeds:
                continue
            embed = mensaje.embeds[0]
            if embed.title and embed.title.startswith("📤 REGISTRO DE"):
                usuario_mencion = embed.title.replace("📤 REGISTRO DE ", "").strip()
                mensajes_por_usuario[usuario_mencion] = mensaje

        print("♻️ Sincronizando mensajes por miembro...")
        miembros_actuales = [m for m in canal.guild.members if not m.bot]
        usuarios_actuales = set()

        for miembro in miembros_actuales:
            usuarios_actuales.add(miembro.mention)
            mensaje_existente = mensajes_por_usuario.get(miembro.mention)
            embed = self.crear_embed_usuario(miembro)

            if mensaje_existente:
                try:
                    await mensaje_existente.edit(embed=embed)
                except Exception as e:
                    print(f"❌ Error al editar mensaje de {miembro.display_name}: {e}")
            else:
                try:
                    await canal.send(embed=embed)
                except Exception as e:
                    print(f"❌ Error al crear mensaje de {miembro.display_name}: {e}")

        print("🧹 Eliminando mensajes sobrantes...")
        for usuario_mencion, mensaje in mensajes_por_usuario.items():
            if usuario_mencion not in usuarios_actuales:
                try:
                    await mensaje.delete()
                except Exception as e:
                    print(f"❌ Error al borrar mensaje sobrante: {e}")

        print("✅ Panel público actualizado.")

    def crear_embed_usuario(self, miembro):
        tz = pytz.timezone("America/Santo_Domingo")
        ahora = datetime.now(tz)
        fecha_hora = ahora.strftime("%A a las %H:%M").capitalize()

        embed = discord.Embed(title=f"📤 REGISTRO DE {miembro.mention}", color=discord.Color.orange())
        embed.set_author(name=miembro.display_name, icon_url=miembro.display_avatar.url)
        embed.add_field(name="Estado actual", value="Activo", inline=False)
        embed.add_field(name="Total de faltas", value="0", inline=True)
        embed.add_field(name="Faltas este mes", value="0", inline=True)
        embed.set_footer(text=f"Sistema automatizado de reputación pública • {fecha_hora}")
        return embed

def setup(bot):
    bot.add_cog(Faltas(bot))
