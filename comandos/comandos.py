import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import redis
import asyncio

CANAL_COMANDOS_ID = int(os.getenv("CANAL_COMANDOS", 1390164280959303831))
GUILD_ID = int(os.getenv("GUILD_ID"))

class Comandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

    async def borrar_mensaje_temporal(self, mensaje):
        await asyncio.sleep(600)  # 10 minutos
        try:
            await mensaje.delete()
        except:
            pass

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema de faltas.")
    async def estado(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal 💻comandos.", ephemeral=True)
            return

        user = interaction.user
        user_id = str(user.id)
        key = f"{GUILD_ID}:faltas:{user_id}"
        datos = self.redis.hgetall(key)

        if not datos:
            datos = {"faltas_total": "0", "faltas_mes": "0", "estado": "activo"}

        embed = discord.Embed(
            title="🧾 Estado actual del usuario",
            color=discord.Color.teal()
        )
        embed.add_field(name="👤 Usuario", value=user.mention, inline=False)
        embed.add_field(name="📆 Faltas este mes", value=datos.get("faltas_mes", "0"), inline=True)
        embed.add_field(name="📊 Faltas totales", value=datos.get("faltas_total", "0"), inline=True)
        embed.add_field(name="📌 Estado actual", value=datos.get("estado", "activo"), inline=True)
        embed.set_footer(text="Sistema automatizado de control • VX")

        try:
            await user.send(embed=embed)
        except:
            pass

        await interaction.response.send_message("✅ Te envié tu estado por DM.", ephemeral=True)
        mensaje = await interaction.channel.send(f"🧾 {user.mention}, tu estado ha sido enviado por DM.")
        await self.borrar_mensaje_temporal(mensaje)

    @app_commands.command(name="estadisticas", description="(Solo admins) Muestra estadísticas generales del servidor.")
    async def estadisticas(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal 💻comandos.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ No tienes permiso para usar este comando.", ephemeral=True)
            return

        miembros = self.redis.keys(f"{GUILD_ID}:faltas:*")
        total_miembros = len(miembros)

        baneados = 0
        expulsados = 0
        activos = 0

        for clave in miembros:
            estado = self.redis.hget(clave, "estado")
            if estado == "baneado":
                baneados += 1
            elif estado == "expulsado":
                expulsados += 1
            else:
                activos += 1

        embed = discord.Embed(
            title="📊 Estadísticas Generales del Servidor",
            color=discord.Color.blue()
        )
        embed.add_field(name="👥 Total de miembros", value=total_miembros, inline=True)
        embed.add_field(name="🟢 Activos", value=activos, inline=True)
        embed.add_field(name="⛔ Baneados", value=baneados, inline=True)
        embed.add_field(name="🚫 Expulsados", value=expulsados, inline=True)
        embed.set_footer(text="Sistema automatizado de control • VX")

        try:
            await interaction.user.send(embed=embed)
        except:
            pass

        await interaction.response.send_message("✅ Las estadísticas han sido enviadas por DM.", ephemeral=True)
        mensaje = await interaction.channel.send(f"📊 {interaction.user.mention}, tus estadísticas han sido enviadas por DM.")
        await self.borrar_mensaje_temporal(mensaje)

    @commands.Cog.listener()
    async def on_ready(self):
        canal = self.bot.get_channel(CANAL_COMANDOS_ID)
        if canal:
            async for mensaje in canal.history(limit=50):
                if mensaje.author == self.bot.user and "📘 Instrucciones de uso de comandos" in mensaje.content:
                    return  # Ya están las instrucciones

            instrucciones = (
                "📘 **Instrucciones de uso de comandos**\n\n"
                "✅ Usa `/estado` para ver tu historial y estatus actual.\n"
                "📊 Usa `/estadisticas` para ver los totales del servidor (solo admins).\n\n"
                "📍 Todos los comandos deben ejecutarse aquí en el canal 💻comandos.\n"
                "🕓 Las respuestas automáticas se eliminan después de 10 minutos para mantener el orden."
            )
            await canal.send(instrucciones)


async def setup(bot):
    await bot.add_cog(Comandos(bot))
