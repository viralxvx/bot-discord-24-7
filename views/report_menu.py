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
        
        if self.reportado.id not in amonestaciones:
            amonestaciones[self.reportado.id] = []
            
        amonestaciones[self.reportado.id] = [
            t for t in amonestaciones[self.reportado.id] 
            if (ahora - t).total_seconds() < 7 * 86400
        ]
        amonestaciones[self.reportado.id].append(ahora)
        cantidad = len(amonestaciones[self.reportado.id])
        
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
                canal_faltas = discord.utils.get(self.autor.guild.text_channels, name="📤faltas")
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
                    canal_faltas = discord.utils.get(self.autor.guild.text_channels, name="📤faltas")
                    if canal_faltas:
                        faltas_dict[self.reportado.id]["estado"] = "Baneado"
                        await actualizar_mensaje_faltas(canal_faltas, self.reportado, faltas_dict[self.reportado.id]["faltas"], faltas_dict[self.reportado.id]["aciertos"], "Baneado")
                except discord.Forbidden:
                    pass
                    
        await interaction.response.send_message("✅ **Reporte registrado**", ephemeral=True)
        await registrar_log(f"Reporte: {self.autor.name} → {self.reportado.name} ({razon})", categoria="reportes")
        save_state()
