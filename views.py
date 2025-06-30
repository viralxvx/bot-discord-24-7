import discord
import datetime
from discord.ui import View, Select
from discord import SelectOption, Interaction
from discord_bot import bot
from config import CANAL_LOGS, CANAL_FALTAS, FAQ_FALLBACK, ADMIN_ID
from state_management import amonestaciones, baneos_temporales, save_state, faltas_dict, active_conversations, ticket_counter, faq_data
from utils import actualizar_mensaje_faltas, registrar_log

class ReportMenu(View):
    def __init__(self, reportado, autor):
        super().__init__(timeout=60)
        self.reportado = reportado
        self.autor = autor
        self.select = Select(
            placeholder="✉️ Selecciona la infracción",
            options=[
                SelectOption(label="RT", description="No hizo retweet"),
                SelectOption(label="LIKE", description="No dio like"),
                SelectOption(label="COMENTARIO", description="No comentó"),
                SelectOption(label="FORMATO", description="Formato incorrecto"),
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: Interaction):
        razon = self.select.values[0].upper()
        ahora = datetime.datetime.now(datetime.timezone.utc)
        
        if self.reportado.id not in amonestaciones:
            amonestaciones[self.reportado.id] = []
            
        amonestaciones[self.reportado.id] = [
            t for t in amonestaciones[self.reportado.id] 
            if (ahora - t).total_seconds() < 7 * 86400
        ]
        amonestaciones[self.reportado.id].append(ahora)
        cantidad = len(amonestaciones[self.reportado.id])
        
        canal_faltas = discord.utils.get(self.autor.guild.text_channels, name=CANAL_FALTAS)
        try:
            await self.reportado.send(
                f"⚠️ **Amonestación por: {razon}**\n"
                f"📌 3 amonestaciones = baneo 7 días"
            )
        except:
            pass
            
        logs_channel = discord.utils.get(self.autor.guild.text_channels, name=CANAL_LOGS)
        if logs_channel:
            await logs_channel.send(
                f"📜 **Reporte**\n"
                f"👤 Reportado: {self.reportado.mention}\n"
                f"📣 Por: {self.autor.mention}\n"
                f"📌 Infracción: `{razon}`\n"
                f"📆 Amonestaciones: `{cantidad}`"
            )
            
        role_baneado = discord.utils.get(self.autor.guild.roles, name="baneado")
        if cantidad >= 6 and baneos_temporales[self.reportado.id]:
            try:
                await self.reportado.send("⛔ **Expulsado permanentemente**")
            except:
                pass
            try:
                await self.autor.guild.kick(self.reportado, reason="Expulsado por reincidencia")
                if canal_faltas:
                    faltas_dict[self.reportado.id]["estado"] = "Expulsado"
                    await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "Expulsado")
            except discord.Forbidden:
                pass
                
        elif cantidad >= 3 and not baneos_temporales[self.reportado.id]:
            if role_baneado:
                try:
                    await self.reportado.send("🚫 **Baneado por 7 días**")
                    await self.reportado.add_roles(role_baneado, reason="3 amonestaciones en 7 días")
                    baneos_temporales[self.reportado.id] = ahora
                    if canal_faltas:
                        faltas_dict[self.reportado.id]["estado"] = "Baneado"
                        await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "Baneado")
                except discord.Forbidden:
                    pass
                    
        await interaction.response.send_message("✅ **Reporte registrado**", ephemeral=True)
        await registrar_log(f"Reporte: {self.autor.name} → {self.reportado.name} ({razon})", categoria="reportes")
        save_state()

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
        if self.select.values[0] == "Generar ticket":
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
                
        elif self.select.values[0] == "Hablar con humano":
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
                
        elif self.select.values[0] == "Cerrar consulta":
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
            
        elif self.select.values[0] in ["✅ ¿Cómo funciona VX?", "✅ ¿Cómo publico mi post?", "✅ ¿Cómo subo de nivel?"]:
            response = faq_data.get(self.select.values[0], FAQ_FALLBACK.get(self.select.values[0], "No se encontró respuesta"))
            await interaction.response.send_message(response, ephemeral=True)
            if user_id in active_conversations:
                active_conversations[user_id]["message_ids"].append(interaction.message.id)
                active_conversations[user_id]["last_time"] = datetime.datetime.now(datetime.timezone.utc)
                
        save_state()
