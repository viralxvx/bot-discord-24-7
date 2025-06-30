# views/support_menu.py
import discord

class SupportMenu(discord.ui.View):
    def __init__(self, author, query):
        super().__init__(timeout=None)
        self.author = author
        self.query = query
        self.select = discord.ui.Select(
            placeholder="Selecciona una opción",
            options=[
                discord.SelectOption(label="Generar ticket", description="Crear un nuevo ticket de soporte", emoji="🎫"),
                discord.SelectOption(label="Hablar con humano", description="Contactar con un administrador", emoji="🧑‍💼"),
                discord.SelectOption(label="Cerrar consulta", description="Cerrar esta consulta", emoji="❌"),
                discord.SelectOption(label="✅ ¿Cómo funciona VX?", description="Preguntas frecuentes sobre VX", emoji="❓"),
                discord.SelectOption(label="✅ ¿Cómo publico mi post?", description="Preguntas frecuentes sobre publicación", emoji="❓"),
                discord.SelectOption(label="✅ ¿Cómo subo de nivel?", description="Preguntas frecuentes sobre niveles", emoji="❓"),
            ]
        )
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        from discord_bot import bot, active_conversations, registrar_log, FAQ_FALLBACK, faq_data, CANAL_SOPORTE, ADMIN_ID
        import datetime

        user_id = self.author.id
        if self.select.values[0] == "Generar ticket":
            # Lógica para generar ticket
            ticket_counter = 1  # Esto debe gestionarse con persistencia en tu código principal
            ticket_id = f"ticket-{ticket_counter:03d}"
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await interaction.response.send_message("❌ **Error al generar ticket**", ephemeral=True)
                return
            try:
                await self.author.send(f"🎫 **Ticket #{ticket_id} generado**")
                await admin.send(f"🎫 **Ticket #{ticket_id}** por {self.author.mention}: '{self.query}'")
                await interaction.response.send_message(f"✅ **Ticket #{ticket_id} generado**", ephemeral=True)
                await registrar_log(f"Ticket #{ticket_id}: {self.author.name}", categoria="soporte")
            except Exception:
                await interaction.response.send_message("❌ **Error al generar ticket**", ephemeral=True)

        elif self.select.values[0] == "Hablar con humano":
            admin = bot.get_user(int(ADMIN_ID))
            if not admin:
                await interaction.response.send_message("❌ **Error al contactar admin**", ephemeral=True)
                return
            try:
                await self.author.send(f"🔧 **Conectado con administrador**")
                await admin.send(f"⚠️ **Soporte solicitado** por {self.author.mention}: '{self.query}'")
                await interaction.response.send_message("✅ **Admin notificado**", ephemeral=True)
            except Exception:
                await interaction.response.send_message("❌ **Error al contactar admin**", ephemeral=True)

        elif self.select.values[0] == "Cerrar consulta":
            from discord_bot import active_conversations
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

        elif self.select.values[0] in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
            response = faq_data.get(self.select.values[0], FAQ_FALLBACK.get(self.select.values[0], "No se encontró respuesta"))
            await interaction.response.send_message(response, ephemeral=True)
            if user_id in active_conversations:
                active_conversations[user_id]["message_ids"].append(interaction.message.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
