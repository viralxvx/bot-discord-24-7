# comandos/publicar_funcion.py

import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_FUNCIONES, ADMIN_ID
import re

class PublicarFuncion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="publicar_funcion",
        description="(Solo admins) Publica una nueva función con formato profesional automáticamente."
    )
    @app_commands.describe(
        titulo="Título visual que aparece arriba del embed",
        descripcion="Texto completo, pegado desde cualquier lugar (Word, Notion, Docs, etc.)"
    )
    async def publicar_funcion(
        self,
        interaction: discord.Interaction,
        titulo: str,
        descripcion: str
    ):
        if interaction.user.id != ADMIN_ID and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("⛔ No tienes permisos para usar este comando.", ephemeral=True)
            return

        canal_funciones = interaction.guild.get_channel(CANAL_FUNCIONES)
        if not canal_funciones:
            await interaction.response.send_message("❌ No se encontró el canal de funciones.", ephemeral=True)
            return

        # 🔍 LIMPIEZA INTELIGENTE
        texto = descripcion.replace('"""', '').replace("```", '').strip()
        texto = re.sub(r'\r\n|\r', '\n', texto)  # Estilo Word a Unix
        texto = re.sub(r'\n{3,}', '\n\n', texto)  # Reemplaza 3+ saltos por doble
        texto = re.sub(r'[ \t]+', ' ', texto)  # Espacios y tabs en exceso

        # 📚 INTENTA DETECTAR BLOQUES LÓGICOS
        bloques = re.split(r'\n\s*\n', texto)
        bloques = [bloque.strip() for bloque in bloques if bloque.strip()]

        # 🖼️ EMBED
        embed = discord.Embed(
            title=f"🎉 {titulo.strip()}",
            color=0x0057b8
        )
        embed.set_thumbnail(url="https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj")

        # 🔎 Si es demasiado largo, convierte en campos
        if len(bloques) == 1:
            embed.description = bloques[0]
        else:
            for i, bloque in enumerate(bloques):
                # Título invisible para que no se repita
                embed.add_field(name="‎" if i == 0 else "​", value=bloque, inline=False)

        embed.set_footer(text="Publicado por VXbot | Sistema premium")
        mensaje = await canal_funciones.send(embed=embed)

        url = f"https://discord.com/channels/{canal_funciones.guild.id}/{canal_funciones.id}/{mensaje.id}"
        await interaction.response.send_message(f"✅ Función publicada con éxito. [Ver en canal]({url})", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PublicarFuncion(bot))

