# comandos/idea_viral.py

import discord
from discord.ext import commands
from discord import app_commands
import openai
from config import OPENAI_API_KEY, CANAL_GPT_ID
from mensajes.asistente_viral_mensajes import INSTRUCCION_IDEA

openai.api_key = OPENAI_API_KEY

class IdeaViral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="gpt_idea_viral",  # Renombrado para evitar conflicto
        description="🧠 Genera una idea viral desde el asistente GPT"
    )
    @app_commands.describe(tema="Tema sobre el que deseas una idea")
    async def idea_viral(self, interaction: discord.Interaction, tema: str):
        if interaction.channel.id != CANAL_GPT_ID:
            await interaction.response.send_message("⛔ Este comando solo está disponible en el canal **VX gpt**.", ephemeral=True)
            return

        await interaction.response.defer()
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            respuesta = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": INSTRUCCION_IDEA},
                    {"role": "user", "content": f"Quiero una idea viral sobre el tema: {tema}"}
                ],
                temperature=0.8,
                max_tokens=700
            )

            idea = respuesta.choices[0].message.content.strip()

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
            print(f"❌ Error con OpenAI: {e}")
            await interaction.followup.send("❌ Ocurrió un error al generar la idea. Notifica al administrador.")

async def setup(bot):
    await bot.add_cog(IdeaViral(bot))
    print("✅ Comando /gpt_idea_viral cargado correctamente.")
