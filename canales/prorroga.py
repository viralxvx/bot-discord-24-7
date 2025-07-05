import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_COMANDOS_ID, REDIS_URL, CANAL_LOGS_ID
from mensajes.inactividad_texto import PRORROGA_ADMIN_OK
import redis
from datetime import datetime, timedelta, timezone
from utils.logger import log_discord

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
        dias="Cantidad de días (por defecto 7, máximo 30)"
    )
    async def prorroga(
        self, interaction: discord.Interaction,
        usuario: discord.Member,
        dias: int = 7
    ):
        if interaction.channel_id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal de comandos.", ephemeral=True
            )
            await log_discord(self.bot, "Intento de usar /prorroga fuera del canal de comandos.", CANAL_LOGS_ID, "warning", "Prorroga")
            return

        if not (interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_guild):
            await interaction.response.send_message(
                "❌ No tienes permisos para usar este comando.", ephemeral=True
            )
            await log_discord(self.bot, f"Usuario sin permisos intentó usar /prorroga: {interaction.user}", CANAL_LOGS_ID, "warning", "Prorroga")
            return

        dias = max(1, min(dias, 30))
        ahora = datetime.now(timezone.utc)
        hasta = ahora + timedelta(days=dias)
        key_prorroga = f"inactividad:prorroga:{usuario.id}"
        self.redis.set(key_prorroga, hasta.isoformat())

        log_msg = f"{interaction.user.display_name} otorgó prórroga a {usuario.display_name} ({usuario.id}) por {dias} días."
        await log_discord(self.bot, log_msg, CANAL_LOGS_ID, "success", "Prorroga")

        embed = discord.Embed(
            title="✅ Prórroga registrada",
            description=f"{usuario.mention} tiene una prórroga de **{dias} días** de inactividad (por admin/mod).",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Otorgada por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, delete_after=600)

        try:
            await usuario.send(PRORROGA_ADMIN_OK.format(usuario=usuario.mention, dias=dias))
        except Exception as e:
            await log_discord(self.bot, f"No se pudo enviar DM a {usuario.display_name}: {e}", CANAL_LOGS_ID, "warning", "Prorroga")

async def setup(bot):
    await bot.add_cog(ProrrogaComando(bot))
