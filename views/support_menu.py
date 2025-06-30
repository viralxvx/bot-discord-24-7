import discord
import datetime
from discord.ui import View, Select
from discord import SelectOption, Interaction
from discord_bot import bot
from config import ADMIN_ID, FAQ_FALLBACK
from state_management import active_conversations, ticket_counter, faq_data, save_state
from utils import registrar_log

class SupportMenu(View):
    def __init__(self, autor, query):
        super().__init__(timeout=60)
        self.autor = autor
        self.query = query
        self.select = Select(
            placeholder="🔧 Selecciona una opción",
            options=[
                SelectOption(label="Generar ticket", description="Crear un ticket para seguimiento"),
                SelectOption(label="Hablar con humano", description="Conectar con un administrador"),
                SelectOption(label="Cerrar consulta", description="Finalizar la interacción"),
                SelectOption(label="✅ ¿Cómo funciona VX?", description="Aprende cómo funciona la comunidad"),
                SelectOption(label="✅ ¿Cómo publico mi post?", description="Pasos para publicar tu contenido"),
                SelectOption(label="✅ ¿Cómo subo de nivel?", description="Cómo avanzar en la comunidad")
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        user_id = self.autor.id
        selected_value = self.select.values[0]
        
        if selected_value == "Generar ticket":
            ticket_counter += 1
            ticket_id = f"ticket-{ticket_counter:03d}"
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await interaction.response.send_message("❌ **Error al generar ticket**", ephemeral=True)
                return
            try:
                await self.autor.send(f"🎫 **Ticket #{ticket_id} generado**")
                await admin.send(f"🎫 **Ticket #{ticket_id}** por {self.autor.mention}: '{self.query}'")
                await interaction.response.send_message(f"✅ **Ticket #{ticket_id} generado**", ephemeral=True)
                await registrar_log(f"Ticket #{ticket_id}: {self.autor.name}", categoria="soporte")
            except Exception:
                await interaction.response.send_message("❌ **Error al generar ticket**", ephemeral=True)
                
        elif selected_value == "Hablar con humano":
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await interaction.response.send_message("❌ **Error al contactar admin**", ephemeral=True)
                return
            try:
                await self.autor.send(f"🔧 **Conectado con administrador**")
                await admin.send(f"⚠️ **Soporte solicitado** por {self.autor.mention}: '{self.query}'")
                await interaction.response.send_message("✅ **Admin notificado**", ephemeral=True)
            except Exception:
                await interaction.response.send_message("❌ **Error al contactar admin**", ephemeral=True)
                
        elif selected_value == "Cerrar consulta":
            from config import CANAL_SOPORTE
            canal_soporte = discord.utils.get(bot.get_all_channels(), name=CANAL_SOPORTE)
            if user_id in active_conversations and "message_ids" in active_conversations[user_id]:
                for msg_id in active_conversations[user_id]["message_ids"]:
                    try:
                        msg = await canal_soporte.fetch_message(msg_id)
                        await msg.delete()
                    except:
                        pass
            if user_id in active_conversations:
                del active_conversations[user_id]
            await interaction.response.send_message("✅ **Consulta cerrada**", ephemeral=True)
            
        elif selected_value in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
            response = faq_data.get(selected_value, FAQ_FALLBACK.get(selected_value, "No se encontró respuesta"))
            await interaction.response.send_message(response, ephemeral=True)
            if user_id in active_conversations:
                active_conversations[user_id]["message_ids"].append(interaction.message.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
                
        save_state()
