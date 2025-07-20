# comandos/hablar.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from config import CANAL_GPT_ID, ASISTENTE_API_URL

class HablarCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hablar", description="🧠 Habla libremente con ChatGPT.")
    @app_commands.describe(mensaje="¿Qué quieres preguntarle o decirle a ChatGPT?")
    async def hablar(self, interaction: discord.Interaction, mensaje: str):
        if interaction.channel.id != CANAL_GPT_ID:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal `VX gpt`.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ASISTENTE_API_URL}/hablar",
                    json={"mensaje": mensaje, "autor": str(interaction.user)}
                ) as respuesta:

                    if respuesta.status == 200:
                        data = await respuesta.json()
                        contenido = data.get("respuesta", "⚠️ No se recibió respuesta del asistente.")

                        await interaction.followup.send(f"🧠 **ChatGPT dice:**\n{contenido}")
                        try:
                            await interaction.user.send(f"🧠 Tu mensaje: **{mensaje}**\n\n📩 **Respuesta de ChatGPT:**\n{contenido}")
                        except:
                            pass
                    else:
                        await interaction.followup.send("❌ Error al procesar la conversación. Notifica al administrador.")

        except Exception as e:
            await interaction.followup.send("❌ Error de conexión con el asistente. Notifica al administrador.")

async def setup(bot):
    await bot.add_cog(HablarCommand(bot))
