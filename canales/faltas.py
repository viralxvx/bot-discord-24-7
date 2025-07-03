import discord
from discord.ext import commands
import os
from config import CANAL_FALTAS_ID, REDIS_URL
import redis

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
        try:
            mensajes_existentes = [m async for m in canal.history(limit=None)]
        except Exception as e:
            print(f"❌ Error al obtener historial: {e}")
            return

        mensajes_por_usuario = {}
        for mensaje in mensajes_existentes:
            if mensaje.author != self.bot.user:
                continue
            if not mensaje.embeds:
                continue
            embed = mensaje.embeds[0]
            if embed.description and embed.description.startswith("📤 REGISTRO DE"):
                usuario_mention = embed.description.split("\n")[0].replace("📤 REGISTRO DE ", "").strip()
                mensajes_por_usuario[usuario_mention] = mensaje

        print("📊 Reconstruyendo panel público de faltas...")
        try:
            for miembro in canal.guild.members:
                if miembro.bot:
                    continue
                await self.generar_o_actualizar_mensaje(canal, miembro, mensajes_por_usuario)
            print("✅ Panel público actualizado.")
        except Exception as e:
            print(f"❌ Error al reconstruir el panel: {e}")

    async def generar_o_actualizar_mensaje(self, canal, miembro, mensajes_existentes):
        estado = "✅ Activo"
        faltas_mes = "0"
        faltas_totales = "0"

        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=miembro.display_name, icon_url=miembro.display_avatar.url)
        embed.description = (
            f"📤 REGISTRO DE {miembro.mention}\n"
            f"Estado actual: {estado}\n"
            f"Total de faltas: {faltas_totales}\n"
            f"Faltas este mes: {faltas_mes}"
        )
        embed.set_footer(text="Sistema automatizado de reputación pública")

        mensaje_existente = mensajes_existentes.get(miembro.mention)
        try:
            if mensaje_existente:
                await mensaje_existente.edit(embed=embed)
            else:
                await canal.send(embed=embed)
        except Exception as e:
            print(f"❌ Error con {miembro.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(Faltas(bot))
