import discord
from discord import app_commands
from discord.ext import commands
import redis
import json
from datetime import datetime
from config import REDIS_URL, ADMIN_ID

MAX_SUGERENCIAS = 10

ESTADOS = {
    "pendiente": ("🔵", discord.Color.blue()),
    "hecha": ("🟢", discord.Color.green()),
    "descartada": ("🔴", discord.Color.red())
}

class VerSugerencias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.paginas = {}  # Guarda el estado de la paginación por usuario
        self.mensajes_originales = {}  # Guarda el mensaje original por usuario para edición

    @app_commands.command(name="ver_sugerencias", description="Ver sugerencias enviadas por los usuarios")
    async def ver_sugerencias(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
            return

        claves = self.redis.keys("sugerencia:*")
        if not claves:
            await interaction.response.send_message("📭 No hay sugerencias registradas.", ephemeral=True)
            return

        claves.sort()
        self.paginas[interaction.user.id] = claves
        await self.mostrar_pagina(interaction, 0, inicial=True)

    async def mostrar_pagina(self, interaction, pagina, inicial=False):
        claves = self.paginas.get(interaction.user.id, [])
        inicio = pagina * MAX_SUGERENCIAS
        fin = inicio + MAX_SUGERENCIAS
        claves_pagina = claves[inicio:fin]

        embeds = []
        components = []

        for clave in claves_pagina:
            sugerencia = self.redis.hgetall(clave)
            estado = sugerencia.get("estado", "pendiente")
            contenido = sugerencia.get("contenido", "[Sin contenido]")
            timestamp = sugerencia.get("fecha", "")
            autor_id = sugerencia.get("usuario_id", None)

            if autor_id:
                try:
                    usuario = await self.bot.fetch_user(int(autor_id))
                    autor = usuario.mention
                except:
                    autor = "Usuario desconocido"
            else:
                autor = "Usuario desconocido"

            emoji_estado, color = ESTADOS.get(estado, ("❔", discord.Color.light_grey()))

            embed = discord.Embed(
                title=f"📬 Sugerencia de {autor}",
                description=f"{emoji_estado} **Estado:** {estado.capitalize()}\n📅 **Fecha:** {timestamp}\n\n🧠 **Contenido:**\n> {contenido}",
                color=color
            )
            embed.set_footer(text=f"Clave Redis: {clave}")
            embeds.append(embed)

            custom_id_base = clave.replace(":", "_")
            row = discord.ui.ActionRow(
                discord.ui.Button(label="Hecha", style=discord.ButtonStyle.success, custom_id=f"hecha_{custom_id_base}"),
                discord.ui.Button(label="Pendiente", style=discord.ButtonStyle.primary, custom_id=f"pendiente_{custom_id_base}"),
                discord.ui.Button(label="Descartada", style=discord.ButtonStyle.danger, custom_id=f"descartada_{custom_id_base}")
            )
            components.append(row)

        navigation = discord.ui.ActionRow()
        if inicio > 0:
            navigation.add_item(discord.ui.Button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary, custom_id="pagina_anterior"))
        if fin < len(claves):
            navigation.add_item(discord.ui.Button(label="Siguiente ➡️", style=discord.ButtonStyle.secondary, custom_id="pagina_siguiente"))
        if navigation.children:
            components.append(navigation)

        if inicial:
            message = await interaction.response.send_message(embeds=embeds, components=components, ephemeral=True)
            self.mensajes_originales[interaction.user.id] = await interaction.original_response()
        else:
            msg = self.mensajes_originales.get(interaction.user.id)
            if msg:
                await msg.edit(embeds=embeds, components=components)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Solo administradores pueden cambiar el estado de sugerencias.", ephemeral=True)
            return

        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("pagina_"):
            pagina_actual = 0
            claves = self.paginas.get(interaction.user.id, [])
            if not claves:
                return

            total_paginas = (len(claves) - 1) // MAX_SUGERENCIAS
            for i in range(total_paginas + 1):
                if interaction.message.embeds[0].footer.text.endswith(claves[i * MAX_SUGERENCIAS]):
                    pagina_actual = i
                    break

            nueva_pagina = pagina_actual - 1 if "anterior" in custom_id else pagina_actual + 1
            await self.mostrar_pagina(interaction, nueva_pagina)
            return

        for estado in ESTADOS:
            if custom_id.startswith(f"{estado}_"):
                clave_base = custom_id[len(estado)+1:].replace("_", ":", 1)
                if self.redis.exists(clave_base):
                    self.redis.hset(clave_base, "estado", estado)
                    await interaction.response.send_message(f"✅ Estado actualizado a **{estado.capitalize()}**.", ephemeral=True)
                    # Refrescar página actual
                    claves = self.paginas.get(interaction.user.id, [])
                    for i in range((len(claves) - 1) // MAX_SUGERENCIAS + 1):
                        if clave_base in claves[i * MAX_SUGERENCIAS:(i + 1) * MAX_SUGERENCIAS]:
                            await self.mostrar_pagina(interaction, i)
                            break
                else:
                    await interaction.response.send_message("❌ No se encontró la sugerencia en Redis.", ephemeral=True)
                return

async def setup(bot):
    await bot.add_cog(VerSugerencias(bot))
