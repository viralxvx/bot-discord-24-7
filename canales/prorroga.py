import discord
from discord.ext import commands
from discord import app_commands
from config import CANAL_COMANDOS_ID, REDIS_URL
from mensajes.inactividad_texto import PRORROGA_ADMIN_OK
import redis
from datetime import datetime, timedelta, timezone

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
        # Solo en el canal comandos
        if interaction.channel_id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal de comandos.", ephemeral=True
            )
            return

        # Solo admins/mods
        if not (interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_guild):
            await interaction.response.send_message(
                "❌ No tienes permisos para usar este comando.", ephemeral=True
            )
            return

        # Límite de días
        dias = max(1, min(dias, 30))

        # Registra la prórroga
        ahora = datetime.now(timezone.utc)
        hasta = ahora + timedelta(days=dias)
        key_prorroga = f"inactividad:prorroga:{usuario.id}"
        self.redis.set(key_prorroga, hasta.isoformat())

        print(f"✅ [PRÓRROGA] {interaction.user.display_name} otorgó prórroga a {usuario.display_name} ({usuario.id}) por {dias} días.")

        # Mensaje público en canal comandos (visible 10 minutos)
        embed = discord.Embed(
            title="✅ Prórroga registrada",
            description=f"{usuario.mention} tiene una prórroga de **{dias} días** de inactividad (por admin/mod).",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Otorgada por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, delete_after=600)

        # DM al usuario beneficiado
        try:
            await usuario.send(PRORROGA_ADMIN_OK.format(usuario=usuario.mention, dias=dias))
        except Exception as e:
            print(f"⚠️ [PRÓRROGA] No se pudo enviar DM a {usuario.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(ProrrogaComando(bot))
