import discord
from discord import app_commands
from discord.ext import commands
from config import REDIS_URL, CANAL_COMANDOS_ID
from mensajes.inactividad_texto import PRORROGA_CONCEDIDA, PRORROGA_ADMIN_OK
import redis
from datetime import datetime, timedelta, timezone

class Prorroga(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(name="prorroga", description="Concede prórroga de inactividad a un usuario (admin/mods).")
    @app_commands.describe(usuario="Usuario al que dar prórroga", dias="Días de prórroga (máximo 7)")
    async def prorroga(self, interaction: discord.Interaction, usuario: discord.Member, dias: int):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message("❌ Solo puedes usar este comando en el canal 💻comandos.", ephemeral=True)
            return
        # Solo admins/mods
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return
        if usuario.bot:
            await interaction.response.send_message("❌ No puedes dar prórroga a bots.", ephemeral=True)
            return
        if dias < 1 or dias > 7:
            await interaction.response.send_message("❌ La prórroga debe ser entre 1 y 7 días.", ephemeral=True)
            return

        ahora = datetime.now(timezone.utc)
        hasta = ahora + timedelta(days=dias)
        self.redis.set(f"inactividad:prorroga:{usuario.id}", hasta.isoformat())
        print(f"⏳ [PRÓRROGA] Prórroga otorgada a {usuario.display_name} ({usuario.id}) hasta {hasta.isoformat()}")

        # DM al usuario
        try:
            await usuario.send(PRORROGA_CONCEDIDA.format(dias=dias))
        except Exception as e:
            print(f"⚠️ [PRÓRROGA] No se pudo enviar DM a {usuario.display_name}: {e}")

        await interaction.response.send_message(
            PRORROGA_ADMIN_OK.format(usuario=usuario.mention, dias=dias),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Prorroga(bot))
