import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import os

# ID del canal exclusivo de comandos
CANAL_COMANDOS = 1390164280959303831
GUILD_ID = int(os.getenv("GUILD_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

class Comandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mensaje_instrucciones.start()

    def cog_unload(self):
        self.mensaje_instrucciones.cancel()

    @tasks.loop(count=1)
    async def mensaje_instrucciones(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(CANAL_COMANDOS)

        if not canal:
            print("❌ No se encontró el canal de comandos.")
            return

        try:
            mensajes = [msg async for msg in canal.history(limit=20)]
            ya_publicado = any("📌 COMANDOS DISPONIBLES EN ESTE CANAL" in msg.content for msg in mensajes if msg.author == self.bot.user)

            if not ya_publicado:
                await canal.send(
                    "**📌 COMANDOS DISPONIBLES EN ESTE CANAL**\n\n"
                    "➡️ `/estado`: Consulta tu estado actual (faltas, sanciones, situación).\n"
                    "➡️ `/estadísticas`: Muestra estadísticas generales del servidor.\n\n"
                    "⚠️ Solo los administradores pueden usar `/estadísticas`.\n"
                    "⏳ Las respuestas aquí durarán 10 minutos y también serán enviadas por DM."
                )
                print("✅ Instrucciones de comandos publicadas en 💻comandos.")
            else:
                print("ℹ️ Instrucciones ya estaban publicadas.")
        except Exception as e:
            print(f"❌ Error al publicar instrucciones: {e}")

    @app_commands.command(name="estado", description="Consulta tu estado actual (faltas, advertencias, sanciones).")
    async def estado(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS:
            await interaction.response.send_message("❌ Este comando solo se puede usar en el canal 💻comandos.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        username = interaction.user.display_name

        embed = discord.Embed(title="📄 Estado actual del usuario", color=discord.Color.orange())
        embed.add_field(name="Usuario", value=username, inline=True)
        embed.add_field(name="Faltas (este mes)", value="2", inline=True)
        embed.add_field(name="Total faltas", value="3", inline=True)
        embed.add_field(name="Estado", value="🟡 Activo con advertencias", inline=False)
        embed.set_footer(text="Consulta generada por el sistema")

        # Enviar al canal de comandos (con autodestrucción)
        canal = interaction.channel
        msg = await canal.send(embed=embed)
        await asyncio.sleep(600)  # 10 minutos
        await msg.delete()

        # Enviar por DM
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            print(f"❌ No se pudo enviar DM a {username} ({user_id})")

    @app_commands.command(name="estadisticas", description="Ver estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS:
            await interaction.response.send_message("❌ Este comando solo se puede usar en el canal 💻comandos.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ No tienes permiso para usar este comando.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(title="📊 Estadísticas del servidor", color=discord.Color.blue())
        embed.add_field(name="Miembros totales", value="120", inline=True)
        embed.add_field(name="Miembros expulsados", value="5", inline=True)
        embed.add_field(name="Miembros baneados", value="2", inline=True)
        embed.set_footer(text="Sistema de gestión automatizado")

        # Enviar al canal de comandos
        canal = interaction.channel
        msg = await canal.send(embed=embed)
        await asyncio.sleep(600)
        await msg.delete()

        # Enviar por DM
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            print(f"❌ No se pudo enviar DM a {interaction.user} ({interaction.user.id})")

async def setup(bot):
    await bot.add_cog(Comandos(bot), guild=discord.Object(id=GUILD_ID))
    print("✅ Módulo cargado: comandos")
