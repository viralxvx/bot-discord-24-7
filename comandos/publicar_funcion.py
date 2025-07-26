# comandos/publicar_funcion.py

import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_FUNCIONES, ADMIN_ID
import re

MAX_FIELD_LENGTH = 1024

class PublicarFuncion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="publicar_funcion",
        description="(Solo admins) Publica una nueva función con formato premium automático."
    )
    @app_commands.describe(
        titulo="Título visual del anuncio",
        descripcion="Texto largo, desde Word o Docs. El bot lo organizará solo."
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

        # Limpieza del texto
        texto = descripcion.replace('"""', '').replace("```", '').strip()
        texto = re.sub(r'\r\n|\r', '\n', texto)
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        texto = re.sub(r'[ \t]+', ' ', texto)

        bloques_raw = re.split(r'\n\s*\n', texto)
        bloques = [b.strip() for b in bloques_raw if b.strip()]

        embed = discord.Embed(
            title=f"🎉 {titulo.strip()}",
            color=0x0057b8
        )
        embed.set_thumbnail(url="https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj")

        for bloque in bloques:
            lineas = bloque.split('\n')
            if len(lineas) > 1 and re.match(r'^([^\w\s]{1,2}|[\w\s]{1,4})? ?[\w\*\[]+', lineas[0]):
                titulo_bloque = lineas[0].strip()
                contenido = '\n'.join(lineas[1:]).strip()
            else:
                titulo_bloque = "‎"
                contenido = bloque

            # Dividir contenido largo en trozos de 1024 caracteres
            partes = [contenido[i:i+MAX_FIELD_LENGTH] for i in range(0, len(content=contenido), MAX_FIELD_LENGTH)]
            for i, parte in enumerate(partes):
                nombre = titulo_bloque if i == 0 else "​"
                embed.add_field(name=nombre, value=parte, inline=False)

        embed.set_footer(text="Publicado por VXbot | Sistema premium")
        mensaje = await canal_funciones.send(embed=embed)

        url_funcion = f"https://discord.com/channels/{canal_funciones.guild.id}/{canal_funciones.id}/{mensaje.id}"
        await interaction.response.send_message(
            f"✅ ¡Función publicada correctamente! [Ver en canal]({url_funcion})",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PublicarFuncion(bot))
