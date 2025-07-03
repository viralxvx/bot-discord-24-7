import discord
from discord.ext import commands
from discord import TextChannel
import os

class Comandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        canal_comandos_id = int(os.getenv("CANAL_COMANDOS"))
        canal: TextChannel = self.bot.get_channel(canal_comandos_id)

        if canal:
            # Elimina mensajes existentes del canal 💻comandos
            try:
                async for msg in canal.history(limit=100):
                    if msg.author == self.bot.user:
                        await msg.delete()
            except Exception as e:
                print(f"❌ Error limpiando canal de comandos: {e}")

            # Envía el mensaje de instrucciones
            embed = discord.Embed(
                title="💻 Comandos disponibles",
                description=(
                    "**/estado [usuario]** → Consulta pública y DM sobre el estado de un usuario.\n"
                    "**/estadisticas** → Muestra estadísticas generales del servidor (solo admins).\n\n"
                    "📌 Solo puedes usar estos comandos en este canal.\n"
                    "🕒 Las respuestas se borran automáticamente tras 10 minutos."
                ),
                color=discord.Color.green()
            )
            await canal.send(embed=embed)
            print("✅ Instrucciones publicadas en canal 💻comandos.")
        else:
            print("❌ Error: No se encontró el canal de comandos.")

async def setup(bot):
    await bot.add_cog(Comandos(bot))

    # Carga comandos individuales
    from comandos.estado import Estado
    from comandos.estadisticas import Estadisticas

    await bot.add_cog(Estado(bot))
    await bot.add_cog(Estadisticas(bot))

    print("✅ Comandos /estado y /estadisticas registrados.")
