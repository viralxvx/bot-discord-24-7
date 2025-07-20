# comandos/idea_viral_proxy.py

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from config import CANAL_GPT_ID, ASISTENTE_API_URL

class IdeaViralProxy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="idea_viral",
        description="🧠 Genera una idea viral para X (usando el asistente GPT)"
    )
    @app_commands.describe(tema="Tema central del hilo viral")
    async def idea_viral(self, interaction: discord.Interaction, tema: str):
        if interaction.channel.id != CANAL_GPT_ID:
            await interaction.response.send_message(
                "⛔ Este comando solo puede usarse en el canal **VX gpt**.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ASISTENTE_API_URL}/gpt/idea",
                    json={"tema": tema, "usuario": interaction.user.name}
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Estado inesperado: {resp.status}")
                    
                    data = await resp.json()
                    idea = data.get("idea")

            embed = discord.Embed(
                title="💡 Idea Viral para X",
                description=idea,
                color=0x1DA1F2
            )
            embed.set_footer(text="Generado por el Asistente Viral | VX")

            await interaction.followup.send(embed=embed)

            try:
                await interaction.user.send(embed=embed)
            except:
                print(f"⚠️ No se pudo enviar DM a {interaction.user.display_name}")

        except Exception as e:
            print(f"❌ Error al contactar API asistente: {e}")
            await interaction.followup.send(
                "❌ Error generando la idea. Notifica al administrador."
            )

async def setup(bot):
    await bot.add_cog(IdeaViralProxy(bot))
    print("✅ Comando /idea_viral (proxy) cargado correctamente.")
