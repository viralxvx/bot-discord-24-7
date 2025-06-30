import discord
import datetime
from discord.ui import View, Select
from discord import SelectOption, Interaction
from discord_bot import bot
from config import CANAL_LOGS
from state_management import amonestaciones, baneos_temporales, save_state, faltas_dict
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
        
        # Inicializar amonestaciones si no existen
        if self.reportado.id not in amonestaciones:
            amonestaciones[self.reportado.id] = []
            
        # Filtrar amonestaciones de los últimos 7 días
        amonestaciones[self.reportado.id] = [
            t for t in amonestaciones[self.reportado.id] 
            if (ahora - t).total_seconds() < 7 * 86400
        ]
        amonestaciones[self.reportado.id].append(ahora)
        cantidad = len(amonestaciones[self.reportado.id])
        
        # Notificar al usuario reportado
        try:
            await self.reportado.send(
                f"⚠️ **Amonestación por: {razon}**\n"
                f"📌 3 amonestaciones = baneo 7 días"
            )
        except discord.Forbidden:
            pass  # El usuario tiene los DMs cerrados
        
        # Registrar en el canal de logs
        logs_channel = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOGS)
        if logs_channel:
            try:
                await logs_channel.send(
                    f"📜 **Reporte**\n"
                    f"👤 Reportado: {self.reportado.mention}\n"
                    f"📣 Por: {self.autor.mention}\n"
                    f"📌 Infracción: `{razon}`\n"
                    f"📆 Amonestaciones: `{cantidad}`"
                )
            except discord.HTTPException:
                pass
            
        # Verificar si se debe expulsar (6 amonestaciones y ya estaba baneado)
        role_baneado = discord.utils.get(interaction.guild.roles, name="baneado")
        if cantidad >= 6 and baneos_temporales.get(self.reportado.id):
            try:
                await self.reportado.send("⛔ **Expulsado permanentemente**")
            except discord.Forbidden:
                pass
            try:
                await interaction.guild.kick(self.reportado, reason="Expulsado por reincidencia")
                canal_faltas = discord.utils.get(interaction.guild.text_channels, name="📤faltas")
                if canal_faltas:
                    faltas_dict[self.reportado.id]["estado"] = "Expulsado"
                    try:
                        await actualizar_mensaje_faltas(canal_faltas, self.reportado, 
                                                       faltas_dict[self.reportado.id]["faltas"],
                                                       faltas_dict[self.reportado.id]["aciertos"],
                                                       "Expulsado")
                    except discord.NotFound:
                        # El mensaje de faltas ya no existe, crear uno nuevo
                        mensaje = await canal_faltas.send(
                            f"👤 **Usuario**: {self.reportado.mention}\n"
                            f"🚨 **Estado de Inactividad**: Expulsado\n"
                        )
                        faltas_dict[self.reportado.id]["mensaje_id"] = mensaje.id
            except discord.Forbidden:
                pass
                
        # Verificar si se debe banear (3 amonestaciones y no está baneado)
        elif cantidad >= 3 and not baneos_temporales.get(self.reportado.id):
            if role_baneado:
                try:
                    await self.reportado.send("🚫 **Baneado por 7 días**")
                    await self.reportado.add_roles(role_baneado, reason="3 amonestaciones en 7 días")
                    baneos_temporales[self.reportado.id] = ahora
                    canal_faltas = discord.utils.get(interaction.guild.text_channels, name="📤faltas")
                    if canal_faltas:
                        faltas_dict[self.reportado.id]["estado"] = "Baneado"
                        try:
                            await actualizar_mensaje_faltas(canal_faltas, self.reportado, 
                                                           faltas_dict[self.reportado.id]["faltas"],
                                                           faltas_dict[self.reportado.id]["aciertos"],
                                                           "Baneado")
                        except discord.NotFound:
                            # El mensaje de faltas ya no existe, crear uno nuevo
                            mensaje = await canal_faltas.send(
                                f"👤 **Usuario**: {self.reportado.mention}\n"
                                f"🚨 **Estado de Inactividad**: Baneado\n"
                            )
                            faltas_dict[self.reportado.id]["mensaje_id"] = mensaje.id
                except discord.Forbidden:
                    pass
                    
        # Responder al autor del reporte
        try:
            await interaction.response.send_message("✅ **Reporte registrado**", ephemeral=True)
        except discord.NotFound:
            # La interacción ya no es válida (puede haber expirado)
            try:
                await interaction.channel.send("✅ **Reporte registrado**")
            except:
                pass
        
        await registrar_log(f"Reporte: {self.autor.name} → {self.reportado.name} ({razon})", categoria="reportes")
        save_state()
