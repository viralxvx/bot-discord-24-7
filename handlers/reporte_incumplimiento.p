import discord
from discord.ext import commands
from discord.ui import View, Select, SelectOption
from config import CANAL_REPORTES, CANAL_LOGS, CANAL_FALTAS
from state_management import amonestaciones, faltas_dict, baneos_temporales, save_state
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

    async def select_callback(self, interaction: discord.Interaction):
        razon = self.select.values[0].upper()
        ahora = discord.utils.utcnow()

        if self.reportado.id not in amonestaciones:
            amonestaciones[self.reportado.id] = []
        amonestaciones[self.reportado.id] = [
            t for t in amonestaciones[self.reportado.id] if (ahora - t).total_seconds() < 7 * 86400
        ]
        amonestaciones[self.reportado.id].append(ahora)
        cantidad = len(amonestaciones[self.reportado.id])

        canal_faltas = discord.utils.get(self.autor.guild.text_channels, name=CANAL_FALTAS)
        logs_channel = discord.utils.get(self.autor.guild.text_channels, name=CANAL_LOGS)
        role_baneado = discord.utils.get(self.autor.guild.roles, name="baneado")

        try:
            await self.reportado.send(
                f"⚠️ **Amonestación por: {razon}**\n"
                f"📌 3 amonestaciones = baneo 7 días"
            )
        except:
            pass

        if logs_channel:
            await logs_channel.send(
                f"📜 **Reporte**\n"
                f"👤 Reportado: {self.reportado.mention}\n"
                f"📣 Por: {self.autor.mention}\n"
                f"📌 Infracción: `{razon}`\n"
                f"📆 Amonestaciones: `{cantidad}`"
            )

        if cantidad >= 6 and baneos_temporales.get(self.reportado.id):
            try:
                await self.reportado.send("⛔ **Expulsado permanentemente**")
                await self.autor.guild.kick(self.reportado, reason="Expulsado por reincidencia")
                if canal_faltas:
                    faltas_dict[self.reportado.id]["estado"] = "Expulsado"
                    await actualizar_mensaje_faltas(
                        canal_faltas,
                        self.reportado,
                        faltas_dict[self.reportado.id]["faltas"],
                        faltas_dict[self.reportado.id]["aciertos"],
                        "Expulsado"
                    )
            except discord.Forbidden:
                pass

        elif cantidad >= 3 and not baneos_temporales.get(self.reportado.id):
            if role_baneado:
                try:
                    await self.reportado.send("🚫 **Baneado por 7 días**")
                    await self.reportado.add_roles(role_baneado, reason="3 amonestaciones en 7 días")
                    baneos_temporales[self.reportado.id] = ahora
                    if canal_faltas:
                        faltas_dict[self.reportado.id]["estado"] = "Baneado"
                        await actualizar_mensaje_faltas(
                            canal_faltas,
                            self.reportado,
                            faltas_dict[self.reportado.id]["faltas"],
                            faltas_dict[self.reportado.id]["aciertos"],
                            "Baneado"
                        )
                except discord.Forbidden:
                    pass

        await interaction.response.send_message("✅ **Reporte registrado**", ephemeral=True)
        await registrar_log(f"Reporte: {self.autor.name} → {self.reportado.name} ({razon})", categoria="reportes")
