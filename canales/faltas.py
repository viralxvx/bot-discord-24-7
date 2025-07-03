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
            if embed.title and embed.title.startswith("📋 Estado de "):
                usuario = embed.fields[0].value  # el @usuario
                mensajes_por_usuario[usuario] = mensaje

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
        embed = discord.Embed(title=f"📋 Estado de {miembro.display_name}", color=discord.Color.orange())
        embed.add_field(name="Usuario", value=miembro.mention, inline=True)
        embed.add_field(name="Faltas (mes)", value="0", inline=True)
        embed.add_field(name="Estado", value="✅ Activo", inline=True)
        embed.set_footer(text="Sistema automatizado de faltas - V𝕏")

        mensaje_existente = mensajes_existentes.get(miembro.mention)
        try:
            if mensaje_existente:
                await mensaje_existente.edit(embed=embed)
            else:
                await canal.send(embed=embed)
        except Exception as e:
            print(f"❌ Error con {miembro.display_name}: {e}")

# 🔧 CORREGIDO: función async
async def setup(bot):
    await bot.add_cog(Faltas(bot))
