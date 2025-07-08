import discord
from discord.ext import commands
from discord import app_commands
from config import ADMIN_ID, REDIS_URL, CANAL_COMANDOS_ID
import redis
from utils.logger import log_discord
from mensajes.soporte_embed import generar_embed_sugerencia

class VerSugerencias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(name="ver_sugerencias", description="Revisa las sugerencias enviadas por los usuarios")
    async def ver_sugerencias(self, interaction: discord.Interaction):
        if interaction.channel_id != CANAL_COMANDOS_ID:
            await interaction.response.send_message("❌ Este comando solo puede usarse en el canal 💻comandos.", ephemeral=True)
            return

        if interaction.user.id != ADMIN_ID and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return

        claves = self.redis.keys("sugerencia:*")
        if not claves:
            await interaction.response.send_message("📭 No hay sugerencias registradas actualmente.", ephemeral=True)
            return

        # Ordenar por fecha
        claves.sort(key=lambda k: self.redis.hget(k, "fecha"), reverse=True)

        paginas = []
        for clave in claves:
            data = self.redis.hgetall(clave)
            embed = generar_embed_sugerencia(data, clave)
            paginas.append(embed)

        if not paginas:
            await interaction.response.send_message("📭 No hay sugerencias para mostrar.", ephemeral=True)
            return

        current_page = 0

        async def update_message(msg):
            view = ControlesPaginacion(paginas, msg, interaction.user)
            await msg.edit(embed=paginas[current_page], view=view)

        class ControlesPaginacion(discord.ui.View):
            def __init__(self, embeds, mensaje, usuario):
                super().__init__(timeout=300)
                self.embeds = embeds
                self.mensaje = mensaje
                self.usuario = usuario

            async def interaction_check(self, i: discord.Interaction):
                return i.user.id == self.usuario.id

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
            async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_page
                if current_page > 0:
                    current_page -= 1
                    await update_message(interaction.message)
                    await interaction.response.defer()

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
            async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_page
                if current_page < len(paginas) - 1:
                    current_page += 1
                    await update_message(interaction.message)
                    await interaction.response.defer()

            @discord.ui.button(label="🟢 Hecha", style=discord.ButtonStyle.success)
            async def hecha(self, interaction: discord.Interaction, button: discord.ui.Button):
                clave = claves[current_page]
                self.redis.hset(clave, "estado", "hecha")
                await update_message(interaction.message)
                await interaction.response.defer()

            @discord.ui.button(label="🟡 Pendiente", style=discord.ButtonStyle.primary)
            async def pendiente(self, interaction: discord.Interaction, button: discord.ui.Button):
                clave = claves[current_page]
                self.redis.hset(clave, "estado", "pendiente")
                await update_message(interaction.message)
                await interaction.response.defer()

            @discord.ui.button(label="🔴 Descartada", style=discord.ButtonStyle.danger)
            async def descartada(self, interaction: discord.Interaction, button: discord.ui.Button):
                clave = claves[current_page]
                self.redis.hset(clave, "estado", "descartada")
                await update_message(interaction.message)
                await interaction.response.defer()

        await interaction.response.send_message(embed=paginas[current_page], view=ControlesPaginacion(paginas, None, interaction.user), ephemeral=True)

async def setup(bot):
    await bot.add_cog(VerSugerencias(bot))
