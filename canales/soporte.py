# canales/soporte.py

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput
from config import CANAL_SOPORTE_ID
from mensajes.soporte_mensajes import MENSAJE_INTRO, OPCIONES_MENU, EXPLICACIONES
from utils.logger import log_discord

class MenuSoporteView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSoporteSelect())

class MenuSoporteSelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Selecciona una opción para obtener ayuda...",
            options=OPCIONES_MENU
        )

    async def callback(self, interaction: discord.Interaction):
        opcion = self.values[0]
        contenido = EXPLICACIONES.get(opcion)

        if not contenido:
            await interaction.response.send_message("❌ Esta opción aún no está disponible.", ephemeral=True)
            return

        await interaction.response.send_message(embed=contenido, ephemeral=True)

        if opcion == "sugerencia":
            modal = SugerenciaModal()
            await interaction.response.send_modal(modal)

class SugerenciaModal(Modal, title="📫 Enviar una sugerencia"):
    sugerencia = TextInput(label="¿Cuál es tu sugerencia?", style=discord.TextStyle.paragraph, required=True)
    usuario = TextInput(label="Tu usuario (opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal_staff = interaction.client.get_channel(CANAL_SOPORTE_ID)  # Puedes cambiar esto a un canal privado de staff
        embed = discord.Embed(
            title="🧠 Nueva sugerencia recibida",
            description=f"**Sugerencia:** {self.sugerencia.value}\n**Usuario:** {self.usuario.value or 'Anónimo'}",
            color=discord.Color.blue()
        )
        await canal_staff.send(embed=embed)
        await interaction.response.send_message("✅ ¡Gracias por tu sugerencia!", ephemeral=True)

class Soporte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def limpiar_y_publicar_mensaje(self):
        canal = self.bot.get_channel(CANAL_SOPORTE_ID)
        if not canal:
            await log_discord(self.bot, "Error", "No se encontró el canal de soporte.", "❌ Error soporte")
            return

        async for mensaje in canal.history(limit=50):
            if mensaje.author == self.bot.user:
                await mensaje.delete()

        await canal.send(embed=MENSAJE_INTRO, view=MenuSoporteView())

    @commands.Cog.listener()
    async def on_ready(self):
        await self.limpiar_y_publicar_mensaje()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_SOPORTE_ID and message.author != self.bot.user:
            await message.delete()
            await message.author.send("📌 Este canal es exclusivo para el soporte automatizado de VX. Usa el menú para explorar opciones.")

async def setup(bot):
    await bot.add_cog(Soporte(bot))
