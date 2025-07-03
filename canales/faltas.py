import discord
from discord.ext import commands
import os
import asyncio
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
        mensajes_existentes = await canal.history(limit=None).flatten()
        mensajes_dict = {}

        for mensaje in mensajes_existentes:
            if mensaje.author != self.bot.user or not mensaje.embeds:
                continue
            embed = mensaje.embeds[0]
            if embed.fields:
                usuario_mention = embed.fields[0].value
                user_id = int(usuario_mention.replace("<@", "").replace(">", "").replace("!", ""))
                mensajes_dict[user_id] = mensaje

        print("📊 Actualizando o creando panel público de faltas...")
        guild = canal.guild

        for miembro in guild.members:
            if miembro.bot:
                continue

            embed = discord.Embed(title=f"📋 Estado de {miembro.display_name}", color=discord.Color.orange())
            embed.add_field(name="Usuario", value=miembro.mention, inline=True)
            embed.add_field(name="Faltas (mes)", value="0", inline=True)
            embed.add_field(name="Estado", value="✅ Activo", inline=True)
            embed.set_footer(text="Sistema automatizado de faltas - V𝕏")

            try:
                if miembro.id in mensajes_dict:
                    await mensajes_dict[miembro.id].edit(embed=embed)
                else:
                    await canal.send(embed=embed)
            except Exception as e:
                print(f"❌ Error al procesar mensaje para {miembro.display_name}: {e}")

        print("✅ Panel público actualizado.")

def setup(bot):
    bot.add_cog(Faltas(bot))
