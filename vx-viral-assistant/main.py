# comandos/idea_viral.py

import discord
from discord.ext import commands
from discord import app_commands
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

    # Comando slash registrado correctamente con descripción de parámetros
    @app_commands.command(
        name="idea_viral",
        description="🧠 Genera una idea creativa para un hilo viral en X"
    )
    @app_commands.describe(tema="Tema central sobre el que quieres la idea")
    async def idea_viral(self, interaction: discord.Interaction, tema: str):
        # Verifica si el comando se ejecuta en los canales correctos
        if interaction.channel.id not in [CANAL_COMANDOS_ID, CANAL_GPT_ID]:
            await interaction.response.send_message(MENSAJE_FUERA_DE_CANAL, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            print(f"🟡 Generando idea para: {tema}")

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

            try:
                await interaction.user.send(embed=embed)
            except:
                print(f"⚠️ No se pudo enviar DM a {interaction.user.display_name}")

        except Exception as e:
            print(f"❌ Error con OpenAI: {e}")
            await interaction.followup.send("❌ Ocurrió un error al generar la idea. Notifica al administrador.")

# Método para que setup_hook lo cargue
async def setup(bot):
    await bot.add_cog(IdeaViral(bot))
    print("✅ Comando /idea_viral cargado correctamente.")
