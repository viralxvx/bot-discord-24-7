# comandos/idea_viral.py

import discord
from discord import app_commands
from discord.ext import commands
import openai
from config import (
    OPENAI_API_KEY,
    CANAL_COMANDOS_ID,
    CANAL_GPT_ID
)
from mensajes.asistente_viral_mensajes import (
    INSTRUCCION_IDEA,
    MENSAJE_FUERA_DE_CANAL
)

openai.api_key = OPENAI_API_KEY

class IdeaViral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="idea_viral",
        description="🧠 Genera una idea creativa para un hilo viral en X (Twitter)"
    )
    async def idea_viral(self, interaction: discord.Interaction, tema: str):
        # Solo permitir en los canales autorizados
        if interaction.channel.id not in [CANAL_COMANDOS_ID, CANAL_GPT_ID]:
            await interaction.response.send_message(MENSAJE_FUERA_DE_CANAL, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            respuesta = openai.ChatCompletion.create(
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

            # Enviar por DM también
            try:
                await interaction.user.send(embed=embed)
            except:
                print(f"⚠️ No se pudo enviar DM a {interaction.user.display_name}")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al generar la idea:\n`{str(e)}`")

# Este método será detectado por setup_hook() en main.py
async def setup(bot):
    await bot.add_cog(IdeaViral(bot))
    print("✅ Comando /idea_viral cargado correctamente.")
