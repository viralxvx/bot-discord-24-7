import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import traceback
from config import CANAL_GPT_ID, ASISTENTE_API_URL

class HablarChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hablar", description="🧠 Habla libremente con ChatGPT.")
    @app_commands.describe(mensaje="¿Qué quieres decirle a ChatGPT?")
    async def hablar(self, interaction: discord.Interaction, mensaje: str):
        if interaction.channel.id != CANAL_GPT_ID:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal VX gpt.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ASISTENTE_API_URL}/idea_viral",
                    json={"prompt": mensaje, "autor": str(interaction.user)}
                ) as respuesta:

                    if respuesta.status == 200:
                        data = await respuesta.json()
                        idea = data.get("respuesta", "⚠️ No se recibió una respuesta válida.")
                        await interaction.followup.send(f"🧠 **ChatGPT dice:**\n{idea}")
                    else:
                        await interaction.followup.send("❌ Error al comunicar con el asistente. Notifica al administrador.")
                        print(f"[ERROR] Código HTTP {respuesta.status}")

        except Exception as e:
            traceback.print_exc()
            await interaction.followup.send("❌ Error interno al procesar tu mensaje.")

async def setup(bot):
    await bot.add_cog(HablarChatGPT(bot))
