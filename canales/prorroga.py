import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_COMANDOS_ID, REDIS_URL, CANAL_LOGS_ID
import redis
from datetime import datetime, timedelta, timezone
from utils.logger import log_discord
import json

class ProrrogaComando(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(
        name="prorroga",
        description="Otorga prórroga de inactividad a un usuario (solo admins/mods)."
    )
    @app_commands.describe(
        usuario="Usuario que recibirá la prórroga",
        dias="Cantidad de días (por defecto 7, máximo 30)",
        motivo="Motivo de la prórroga (opcional, recomendado)"
    )
    async def prorroga(
        self, interaction: discord.Interaction,
        usuario: discord.Member,
        dias: int = 7,
        motivo: str = "No especificado"
    ):
        # Solo canal de comandos
        if interaction.channel_id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal de comandos.",
                ephemeral=True
            )
            await log_discord(self.bot, "Intento de usar /prorroga fuera del canal de comandos.", CANAL_LOGS_ID, "warning", "Prorroga")
            return

        # Solo admins o mods
        if not (interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_guild):
            await interaction.response.send_message(
                "❌ No tienes permisos para usar este comando.",
                ephemeral=True
            )
            await log_discord(self.bot, f"Usuario sin permisos intentó usar /prorroga: {interaction.user}", CANAL_LOGS_ID, "warning", "Prorroga")
            return

        if usuario.bot:
            await interaction.response.send_message(
                "❌ No puedes dar prórroga a bots.", ephemeral=True
            )
            return

        dias = max(1, min(dias, 30))
        ahora = datetime.now(timezone.utc)
        hasta = ahora + timedelta(days=dias)
        key_prorroga = f"inactividad:prorroga:{usuario.id}"
        self.redis.set(key_prorroga, hasta.isoformat())

        # Guardar historial
        entry = {
            "fecha": ahora.strftime("%Y-%m-%d %H:%M"),
            "otorgada_por": interaction.user.display_name,
            "duracion": f"{dias} días",
            "motivo": motivo
        }
        self.redis.rpush(f"prorrogas_historial:{usuario.id}", json.dumps(entry))

        log_msg = f"{interaction.user.display_name} otorgó prórroga a {usuario.display_name} ({usuario.id}) por {dias} días. Motivo: {motivo}"
        await log_discord(self.bot, log_msg, CANAL_LOGS_ID, "success", "Prorroga")

        embed = discord.Embed(
            title="✅ Prórroga registrada",
            description=f"{usuario.mention} tiene una prórroga de **{dias} días**.\n\n**Motivo:** {motivo}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Otorgada por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, delete_after=600)

        # DM al usuario
        try:
            await usuario.send(
                f"⏳ Se te ha otorgado una prórroga de **{dias} días** de inactividad por el motivo: **{motivo}**. ¡Aprovecha para ponerte al día y evitar sanciones!"
            )
        except Exception as e:
            await log_discord(self.bot, f"No se pudo enviar DM a {usuario.display_name}: {e}", CANAL_LOGS_ID, "warning", "Prorroga")

        # Actualiza panel de reputación embed
        await actualizar_panel_faltas(self.bot, usuario)

async def setup(bot):
    await bot.add_cog(ProrrogaComando(bot))
