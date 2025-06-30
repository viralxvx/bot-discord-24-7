import discord
import datetime
from config import ADMIN_ID, CANAL_SOPORTE
from views.support_menu import SupportMenu
from utils import registrar_log, faq_data, FAQ_FALLBACK
from state_management import active_conversations

ticket_counter = 0  # Contador de tickets para identificación

async def manejar_soporte(message, bot):
    user_id = message.author.id
    ahora = datetime.datetime.now(datetime.timezone.utc)

    if user_id not in active_conversations:
        active_conversations[user_id] = {
            "message_ids": [],
            "last_time": ahora
        }

    contenido = message.content.lower().strip()

    if contenido in ["salir", "cancelar", "fin"]:
        msg = await message.channel.send("✅ **Consulta cerrada**")
        active_conversations[user_id]["message_ids"].append(msg.id)
        active_conversations[user_id]["last_time"] = ahora
        await message.delete()
        del active_conversations[user_id]
        return

    elif contenido == "ver reglas":
        from handlers.normas_generales import MENSAJE_NORMAS
        msg = await message.channel.send(MENSAJE_NORMAS)
        active_conversations[user_id]["message_ids"].append(msg.id)
        active_conversations[user_id]["last_time"] = ahora
        await message.delete()
        return

    msg = await message.channel.send("👋 **Selecciona una opción**", view=SupportMenu(message.author, message.content))
    active_conversations[user_id]["message_ids"].append(msg.id)
    active_conversations[user_id]["last_time"] = ahora
    await message.delete()

async def manejar_seleccion_soporte(interaction, bot, self):
    global ticket_counter
    user_id = self.autor.id

    seleccion = self.select.values[0]

    if seleccion == "Generar ticket":
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

    elif seleccion == "Hablar con humano":
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

    elif seleccion == "Cerrar consulta":
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

    elif seleccion in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
        response = faq_data.get(seleccion, FAQ_FALLBACK.get(seleccion, "No se encontró respuesta"))
        await interaction.response.send_message(response, ephemeral=True)
        if user_id in active_conversations:
            active_conversations[user_id]["message_ids"].append(interaction.message.id)
            active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
