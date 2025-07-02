# cogs/support_proroga.py

import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import time

import config
from utils.embed_generator import create_proroga_request_embed, format_timestamp, get_current_timestamp

# --- Definición de Vistas y Modales de Discord UI ---

# Clase para el Select Menu (Dropdown) en el mensaje principal de Soporte
class ProrogaSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Selecciona una opción de soporte...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Solicitar Prórroga de Inactividad", value="request_proroga", emoji="⏳", description="Extiende tu periodo de inactividad."),
                # Aquí puedes añadir más opciones de soporte en el futuro
                # discord.SelectOption(label="Reportar un Problema", value="report_problem", emoji="🚨"),
                # discord.SelectOption(label="Sugerencias", value="suggestions", emoji="💡"),
            ],
            custom_id="main_support_select" # ID único para este Select
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "request_proroga":
            # Mostrar el modal de solicitud de prórroga
            proroga_modal = ProrogaModal(title="Solicitud de Prórroga")
            await interaction.response.send_modal(proroga_modal)
            # El resto de la lógica de prórroga se maneja en el callback del modal

# Clase para la View que contiene el Select Menu
class SupportMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout=None para que la vista sea persistente
        self.add_item(ProrogaSelect())
        # Asegúrate de que los botones/selects usen custom_id únicos si añades más

# Clase para el Modal (formulario emergente) de solicitud de prórroga
class ProrogaModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.reason = discord.ui.TextInput(
            label="Razón detallada de tu inactividad",
            placeholder="Ej: Estaré de viaje sin acceso a internet, examen final, etc.",
            style=discord.TextStyle.paragraph,
            min_length=20,
            required=True
        )
        self.add_item(self.reason)

        self.duration = discord.ui.TextInput(
            label="Duración estimada (ej. '5 días', 'hasta el 15/07')",
            placeholder="Opcional. Máximo 30 días.",
            max_length=50,
            required=False
        )
        self.add_item(self.duration)

    async def on_submit(self, interaction: discord.Interaction):
        # Aquí se procesa la solicitud después de que el usuario envíe el modal
        user = interaction.user
        reason = self.reason.value
        duration_str = self.duration.value

        # Notificar al usuario que la solicitud ha sido enviada
        await interaction.response.send_message(
            f"✅ Tu solicitud de prórroga ha sido enviada. Un moderador la revisará pronto.",
            ephemeral=True # Solo el usuario ve este mensaje
        )

        # Crear el embed para el canal de soporte para los moderadores
        proroga_embed = create_proroga_request_embed(
            user=user,
            reason=reason,
            duration_str=duration_str,
            status="PENDIENTE"
        )

        # Enviar la solicitud al canal de soporte para que los moderadores la aprueben/denieguen
        support_channel = interaction.guild.get_channel(config.CANAL_SOPORTE_ID)
        if support_channel:
            # Crear una vista con botones de Aprobación/Denegación
            approval_view = ProrogaApprovalView(user_id=user.id, reason=reason, duration_str=duration_str)
            request_message = await support_channel.send(embed=proroga_embed, view=approval_view)
        else:
            print(f"ERROR: Canal de soporte (ID: {config.CANAL_SOPORTE_ID}) no encontrado para enviar solicitud de prórroga.")
            await user.send("Lo siento, no pude enviar tu solicitud de prórroga al canal de soporte. Por favor, contacta a un administrador.")


# Clase para la View con botones de Aprobación/Denegación para moderadores
class ProrogaApprovalView(discord.ui.View):
    def __init__(self, user_id: int, reason: str, duration_str: str):
        super().__init__(timeout=None) # Timeout=None si quieres que persistan los botones
        self.user_id = user_id
        self.reason = reason
        self.duration_str = duration_str

    @discord.ui.button(label="Aprobar", style=discord.ButtonStyle.success, emoji="✅", custom_id="proroga_approve")
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_proroga_action(interaction, "approve")

    @discord.ui.button(label="Denegar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="proroga_deny")
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_proroga_action(interaction, "deny")

    async def _handle_proroga_action(self, interaction: discord.Interaction, action: str):
        # Verificar si el usuario que interactúa tiene el rol de moderador
        moderator_role = interaction.guild.get_role(config.ROLE_MODERADOR_ID)
        if not moderator_role or moderator_role not in interaction.user.roles:
            await interaction.response.send_message("❌ No tienes permisos para realizar esta acción.", ephemeral=True)
            return

        user_to_affect = interaction.guild.get_member(self.user_id)
        if not user_to_affect:
            await interaction.response.send_message("Usuario no encontrado en el servidor.", ephemeral=True)
            return
        
        bot = interaction.client # Acceso al bot instance

        # Deshabilitar botones después de la acción
        for item in self.children:
            item.disabled = True
        
        if action == "approve":
            # Modal para que el moderador indique la duración
            duration_modal = ProrogaDurationModal(title=f"Duración para {user_to_affect.display_name}", interaction=interaction, user_id=self.user_id, reason=self.reason, duration_str=self.duration_str)
            await interaction.response.send_modal(duration_modal)

        elif action == "deny":
            # Actualizar el embed a DENEGADO
            new_embed = create_proroga_request_embed(
                user=user_to_affect,
                reason=self.reason,
                duration_str=self.duration_str,
                status="DENEGADA",
                moderator=interaction.user
            )
            await interaction.message.edit(embed=new_embed, view=self) # Actualiza la vista para deshabilitar botones
            await interaction.followup.send(f"❌ Solicitud de prórroga para {user_to_affect.mention} denegada por {interaction.user.mention}.", ephemeral=False)
            
            # Notificar al usuario denegado
            try:
                await user_to_affect.send(
                    f"Hola {user_to_affect.mention},\n\n"
                    f"Tu solicitud de prórroga ha sido **denegada** por {interaction.user.mention}.\n"
                    f"Razón solicitada: '{self.reason}'.\n"
                    f"Por favor, asegúrate de cumplir con las normas de publicación para evitar sanciones."
                )
            except discord.Forbidden:
                print(f"No se pudo enviar DM a {user_to_affect.display_name} para notificar denegación de prórroga.")

# Modal para que el moderador ingrese la duración de la prórroga aprobada
class ProrogaDurationModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction, user_id: int, reason: str, duration_str: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_interaction = interaction # Guardar la interacción original para followup
        self.user_id = user_id
        self.reason = reason
        self.duration_str = duration_str # Razón original del usuario

        self.duration_input = discord.ui.TextInput(
            label=f"¿Cuántos días de prórroga se otorgan? (Máx {config.MAX_PRORROGA_DAYS})",
            placeholder="Ej: 7",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.duration_input)

    async def on_submit(self, interaction: discord.Interaction):
        moderator = interaction.user
        granted_days_str = self.duration_input.value
        
        try:
            granted_days = int(granted_days_str)
            if not 1 <= granted_days <= config.MAX_PRORROGA_DAYS:
                await interaction.response.send_message(f"La duración debe ser un número entre 1 y {config.MAX_PRORROGA_DAYS} días. Por favor, intenta de nuevo.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Entrada inválida. Por favor, ingresa un número de días válido.", ephemeral=True)
            return

        user_to_affect = interaction.guild.get_member(self.user_id)
        if not user_to_affect:
            await interaction.response.send_message("Usuario no encontrado en el servidor.", ephemeral=True)
            return

        # Calcular el fin de la prórroga
        proroga_end_timestamp = get_current_timestamp() + (granted_days * 86400) # Días a segundos
        
        # Guardar en Redis
        await interaction.client.redis_state.set_inactivity_extension_end(self.user_id, proroga_end_timestamp)
        await interaction.client.redis_state.set_last_proroga_reason(self.user_id, self.reason) # Guardar la razón
        
        # Notificar al usuario aprobado
        try:
            await user_to_affect.send(
                f"Hola {user_to_affect.mention},\n\n"
                f"Tu solicitud de prórroga ha sido **APROBADA** por {moderator.mention} por **{granted_days} días**.\n"
                f"Tu prórroga es válida hasta el **{format_timestamp(proroga_end_timestamp)}**.\n\n"
                f"Durante este período, el sistema de inactividad te ignorará. "
                f"Asegúrate de retomar la actividad o solicitar una nueva prórroga antes de esta fecha "
                f"para evitar sanciones automáticas."
            )
        except discord.Forbidden:
            print(f"No se pudo enviar DM a {user_to_affect.display_name} para notificar aprobación de prórroga.")

        # Actualizar el embed en el canal de soporte a APROBADA
        new_embed = create_proroga_request_embed(
            user=user_to_affect,
            reason=self.reason,
            duration_str=self.duration_str,
            status="APROBADA",
            moderator=moderator,
            approved_until=proroga_end_timestamp
        )
        # Necesitamos el mensaje original para editarlo. El view.message de la interacción original es útil aquí.
        # Deshabilitar los botones de la vista original
        for item in self.original_interaction.message.components[0].children: # Accede a los botones de la fila
            item.disabled = True
        
        await self.original_interaction.message.edit(embed=new_embed, view=None) # Eliminar la vista
        
        await interaction.response.send_message(f"✅ Prórroga de {user_to_affect.mention} aprobada por {moderator.mention} por {granted_days} días.", ephemeral=False)

        # Actualizar la tarjeta de faltas del usuario
        faltas_manager_cog = interaction.client.get_cog("FaltasManager")
        if faltas_manager_cog:
            await faltas_manager_cog.update_user_fault_card(
                user=user_to_affect,
                status="prorroga",
                last_post_time=await interaction.client.redis_state.get_last_post_time(user_to_affect.id),
                inactivity_extension_end=proroga_end_timestamp,
                proroga_reason=self.reason
            )


# --- Cog principal de Soporte y Prórrogas ---
class SupportProroga(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis_state = bot.redis_state

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Rutina al inicio para asegurar que el mensaje del menú de soporte exista y esté persistente.
        """
        await self.bot.wait_until_ready()
        print("Iniciando setup del canal de soporte...")
        support_channel = self.bot.get_channel(config.CANAL_SOPORTE_ID)
        if not support_channel:
            print(f"ERROR: Canal de soporte (ID: {config.CANAL_SOPORTE_ID}) no encontrado.")
            if config.CANAL_LOGS_ID:
                log_channel = self.bot.get_channel(config.CANAL_LOGS_ID)
                if log_channel:
                    await log_channel.send(f"⚠️ Error: El canal de soporte (ID: `{config.CANAL_SOPORTE_ID}`) no fue encontrado. El menú de soporte no funcionará.")
            return

        # Añadir la vista persistente para que Discord la recuerde entre reinicios
        self.bot.add_view(SupportMenuView())

        # Intentar recuperar el mensaje del menú de soporte si ya existe
        menu_message_id = await self.redis_state.get_soporte_menu_message_id()
        menu_message = None

        if menu_message_id:
            try:
                menu_message = await support_channel.fetch_message(menu_message_id)
                # Opcional: Si el contenido del mensaje fijo ha cambiado, editarlo
                if menu_message.content != config.SOPORTE_MENU_CONTENT:
                    await menu_message.edit(content=config.SOPORTE_MENU_CONTENT)
                print(f"Mensaje del menú de soporte recuperado: {menu_message.id}")
            except discord.NotFound:
                print("Mensaje del menú de soporte no encontrado en Discord, creándolo de nuevo.")
                menu_message_id = None # Forzar la creación
            except discord.Forbidden:
                print("ERROR: No tengo permisos para leer/editar el mensaje del menú de soporte.")
                menu_message_id = None
            except Exception as e:
                print(f"ERROR inesperado al gestionar el mensaje del menú de soporte: {e}")
                menu_message_id = None

        # Si no se encontró o se marcó para crear, enviar un nuevo mensaje
        if not menu_message_id:
            try:
                menu_message = await support_channel.send(content=config.SOPORTE_MENU_CONTENT, view=SupportMenuView())
                await self.redis_state.set_soporte_menu_message_id(menu_message.id)
                print(f"Mensaje del menú de soporte creado y guardado: {menu_message.id}")
            except discord.Forbidden:
                print("ERROR: No tengo permisos para enviar mensajes en el canal de soporte.")
                return

        # Limpiar otros mensajes en el canal de soporte que no sean el menú
        async for message in support_channel.history(limit=50): # Limita el historial a limpiar
            if message.id != menu_message.id and message.author.bot: # Solo mensajes del bot que no sean el menú
                try:
                    await message.delete()
                    print(f"Mensaje antiguo del bot eliminado en #soporte: {message.id}")
                except discord.Forbidden:
                    print("ERROR: No tengo permisos para borrar mensajes antiguos en #soporte.")
                except Exception as e:
                    print(f"ERROR al eliminar mensaje antiguo en #soporte: {e}")
            elif message.id != menu_message.id and not message.author.bot: # Mensajes de usuarios
                # Opcional: Eliminar mensajes de usuarios que no son interacciones de botones/modals
                # Esto es más complejo ya que las interacciones del modal no generan mensajes visibles.
                # Por ahora, se dejarán los mensajes de usuario si no son interacciones.
                pass 
        
        print("Setup del canal de soporte completado.")

async def setup(bot):
    await bot.add_cog(SupportProroga(bot))
