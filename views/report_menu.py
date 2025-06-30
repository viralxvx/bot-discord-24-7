# views/report_menu.py
import discord

class ReportMenu(discord.ui.View):
    def __init__(self, reported_user, reporter):
        super().__init__(timeout=None)
        self.reported_user = reported_user
        self.reporter = reporter

    @discord.ui.button(label="Confirmar reporte", style=discord.ButtonStyle.danger, custom_id="confirm_report")
    async def confirm_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.reporter:
            await interaction.response.send_message("⚠️ Solo el usuario que reportó puede confirmar.", ephemeral=True)
            return
        # Aquí puedes añadir lógica para manejar el reporte, por ejemplo, enviar a un canal de logs o base de datos
        await interaction.response.send_message(f"Reporte confirmado contra {self.reported_user.mention}. Gracias por reportar.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, custom_id="cancel_report")
    async def cancel_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.reporter:
            await interaction.response.send_message("⚠️ Solo el usuario que reportó puede cancelar.", ephemeral=True)
            return
        await interaction.response.send_message("Reporte cancelado.", ephemeral=True)
        self.stop()
