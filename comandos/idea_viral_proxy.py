# comandos/idea_viral_proxy.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import traceback
from config import CANAL_GPT_ID, ASISTENTE_API_URL

class IdeaViralProxy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="idea_viral", description="💡 Genera una idea viral personalizada para X.")
    async def idea_viral(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_GPT_ID:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal VX gpt.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        try:
            payload = {
                "usuario": interaction.user.name,
                "user_id": interaction.user.id
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{ASISTENTE_API_URL}/generar_idea", json=payload) as respuesta:
                    print(f"[DEBUG] Status respuesta API: {respuesta.status}")
                    if respuesta.status == 200:
                        data = await respuesta.json()
                        idea = data.get("idea", "⚠️ No se recibió una idea.")
                        await interaction.followup.send(f"💡 **Idea viral generada:**\n{idea}")
                    else:
                        print(f"[ERROR] Código HTTP {respuesta.status}")
                        text = await respuesta.text()
                        print(f"[ERROR] Respuesta completa: {text}")
                        await interaction.followup.send("❌ Error generando la idea. Notifica al administrador.")
        except Exception as e:
            print(f"❌ Error en idea_viral_proxy: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Error generando la idea. Notifica al administrador.")

async def setup(bot):
    await bot.add_cog(IdeaViralProxy(bot))
