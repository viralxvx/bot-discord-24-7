# canales/soporte.py

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput
from config import CANAL_SOPORTE_ID, REDIS_URL
from mensajes.soporte_mensajes import MENSAJE_INTRO, OPCIONES_MENU, EXPLICACIONES
from utils.logger import log_discord
import redis
import json

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

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
        contenido = {
            "autor_id": str(interaction.user.id),
            "usuario_visible": self.usuario.value or "Anónimo",
            "sugerencia": self.sugerencia.value
        }

        clave = f"sugerencia:{interaction.user.id}:{interaction.id}"
        redis_client.set(clave, json.dumps(contenido))

        await interaction.response.send_message("✅ ¡Gracias por tu sugerencia! La hemos guardado correctamente.", ephemeral=True)

class Soporte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def iniciar_soporte(self):
        canal = self.bot.get_channel(CANAL_SOPORTE_ID)
        if not canal:
            await log_discord(self.bot, "Error", "No se encontró el canal de soporte.", "❌ Error soporte")
            return

        mensajes_fijados = await canal.pins()
        mensaje_bot = next((m for m in mensajes_fijados if m.author == self.bot.user), None)

        if mensaje_bot:
            # Edita el mensaje si cambia el contenido o estructura
            await mensaje_bot.edit(embed=MENSAJE_INTRO, view=MenuSoporteView())
        else:
            mensaje = await canal.send(embed=MENSAJE_INTRO, view=MenuSoporteView())
            await mensaje.pin()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.iniciar_soporte()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == CANAL_SOPORTE_ID and message.author != self.bot.user:
            await message.delete()
            try:
                await message.author.send(
                    "📌 Este canal es exclusivo para el soporte automatizado de VX.\n"
                    "Usa el mensaje fijado para enviar sugerencias o recibir ayuda."
                )
            except:
                pass

async def setup(bot):
    await bot.add_cog(Soporte(bot))
