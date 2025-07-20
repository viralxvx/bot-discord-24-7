# comandos/idea_viral_proxy.py

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from config import CANAL_GPT_ID, ASISTENTE_API_URL

class IdeaViralProxy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="idea_viral",
        description="🧠 Genera una idea viral con el asistente de X"
    )
    @app_commands.describe(tema="Tema central del contenido")
    async def idea_viral(self, interaction: discord.Interaction, tema: str):
        if interaction.channel.id != CANAL_GPT_ID:
            await interaction.response.send_message("⛔ Usa este comando en el canal **VX gpt**", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ASISTENTE_API_URL}/gpt/idea",  # ejemplo de endpoint
                    json={"tema": tema, "usuario": interaction.user.name}
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Respuesta inesperada: {resp.status}")
                    
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
                pass

        except Exception as e:
            print(f"❌ Error al consultar la API: {e}")
            await interaction.followup.send("❌ No se pudo generar la idea. Intenta más tarde.")

async def setup(bot):
    await bot.add_cog(IdeaViralProxy(bot))
    print("✅ Comando /idea_viral (proxy) cargado correctamente.")
