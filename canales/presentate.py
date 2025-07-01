# canales/presentate.py
import discord
from discord.ext import commands
from config import (
    CANAL_PRESENTATE, CANAL_GUIAS_ID, CANAL_NORMAS_GENERALES_ID,
    CANAL_VICTORIAS_ID, CANAL_ESTRATEGIAS_PROBADAS_ID, CANAL_ENTRENAMIENTO_ID
)
from canales.logs import registrar_log # Asegúrate de que esta importación sea correcta

# --- View con el menú desplegable ---
class WelcomeMenuView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None) # Timeout=None para que la vista persista indefinidamente
        self.bot = bot
        self.add_item(self.create_channel_select())

    def create_channel_select(self):
        # Opciones para el menú desplegable. Los 'value' son los IDs de los canales.
        options = [
            discord.SelectOption(label="Lee las Guías", description="Información esencial para empezar.", value=str(CANAL_GUIAS_ID), emoji="📖"),
            discord.SelectOption(label="Revisa las Normas Generales", description="Reglas del servidor.", value=str(CANAL_NORMAS_GENERALES_ID), emoji="✅"),
            discord.SelectOption(label="Mira las Victorias", description="Inspírate con los éxitos de otros.", value=str(CANAL_VICTORIAS_ID), emoji="🏆"),
            discord.SelectOption(label="Estudia las Estrategias Probadas", description="Tácticas para crecer en 𝕏.", value=str(CANAL_ESTRATEGIAS_PROBADAS_ID), emoji="♟️"),
            discord.SelectOption(label="Solicita ayuda en Entrenamiento", description="Obtén soporte para tu primer post.", value=str(CANAL_ENTRENAMIENTO_ID), emoji="🏋️")
        ]
        return ChannelSelect(options=options, bot=self.bot)

class ChannelSelect(discord.ui.Select):
    def __init__(self, options, bot):
        super().__init__(placeholder="Elige una sección para ir directamente...", min_values=1, max_values=1, options=options)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        selected_channel_id = int(self.values[0])
        
        # Verificar si el ID del canal es un valor por defecto (0), lo que indica no configurado
        if selected_channel_id == 0:
            await interaction.response.send_message(
                "⚠️ **¡Ups!** Parece que este canal aún no ha sido configurado por los administradores. Por favor, informa a un mod.",
                ephemeral=True # Solo visible para el usuario
            )
            # Registrar el intento de seleccionar un canal no configurado
            await registrar_log(
                f"Alerta: Usuario {interaction.user.name} intentó seleccionar un canal no configurado (ID: {selected_channel_id}) en el menú de bienvenida.",
                interaction.user, interaction.channel, self.bot
            )
            return

        channel = self.bot.get_channel(selected_channel_id)
        if channel:
            await interaction.response.send_message(
                f"¡Genial! Dirígete a {channel.mention} para más información.",
                ephemeral=True # Solo visible para el usuario
            )
            # Registrar la selección exitosa del canal
            await registrar_log(
                f"Usuario {interaction.user.name} seleccionó el canal {channel.name} (<#{selected_channel_id}>) del menú de bienvenida.",
                interaction.user, interaction.channel, self.bot
            )
        else:
            await interaction.response.send_message(
                "Lo siento, no pude encontrar ese canal. Es posible que haya sido eliminado o no esté visible para ti.",
                ephemeral=True # Solo visible para el usuario
            )
            # Registrar el error si el canal no se encuentra
            await registrar_log(
                f"Error: No se encontró el canal (ID: {selected_channel_id}) seleccionado por {interaction.user.name} en el menú de bienvenida. El canal podría no existir o no ser accesible.",
                interaction.user, interaction.channel, self.bot
            )


# --- Cog Principal para el canal de Presentación ---
class PresentateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Ignorar bots que se unen
        if member.bot:
            return

        # Obtener el canal de presentación
        channel = self.bot.get_channel(CANAL_PRESENTATE)
        if not channel:
            print(f"ERROR: No se pudo encontrar el canal de presentación con la ID: {CANAL_PRESENTATE}")
            await registrar_log(f"ERROR: No se pudo encontrar el canal de presentación ID: {CANAL_PRESENTATE} al unirse {member.name}.", self.bot.user, None, self.bot)
            return

        # Construir el mensaje de bienvenida
        # Usamos <#CHANNEL_ID> para que Discord cree menciones de canal clicables
        welcome_message_text = (
            f"👋 ¡Bienvenid@ a VX {member.mention}!\n"
            f"Sigue estos pasos:\n"
            f"📖 Lee las 3 <#{CANAL_GUIAS_ID}>\n"
            f"✅ Revisa las <#{CANAL_NORMAS_GENERALES_ID}>\n"
            f"🏆 Mira las <#{CANAL_VICTORIAS_ID}>\n"
            f"♟ Estudia las <#{CANAL_ESTRATEGIAS_PROBADAS_ID}>\n"
            f"🏋️ Luego solicita ayuda para tu primer post en <#{CANAL_ENTRENAMIENTO_ID}>\n"
            f"Juntos somos más 🚀\n\n"
            f"Puedes usar el menú desplegable de abajo para ir directamente a cada sección."
        )

        try:
            # Enviar el mensaje con la vista (menú desplegable)
            # La vista se pasa al enviar el mensaje para que los componentes interactivos funcionen.
            sent_message = await channel.send(welcome_message_text, view=WelcomeMenuView(self.bot))
            print(f"Mensaje de bienvenida enviado a {member.name} en #{channel.name} (ID: {sent_message.id})")
            await registrar_log(f"Mensaje de bienvenida a nuevo miembro {member.name} enviado en #{channel.name}", member, channel, self.bot)
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para enviar mensajes en el canal '{channel.name}'.")
            await registrar_log(f"ERROR: Permisos insuficientes para enviar mensaje en {channel.name} para {member.name}", self.bot.user, channel, self.bot)
        except Exception as e:
            print(f"ERROR al enviar mensaje de bienvenida a {member.name}: {e}")
            await registrar_log(f"ERROR inesperado al enviar mensaje de bienvenida a {member.name}: {e}", self.bot.user, channel, self.bot)

async def setup(bot):
    await bot.add_cog(PresentateCog(bot))
