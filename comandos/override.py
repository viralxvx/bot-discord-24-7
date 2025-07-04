import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ID, CANAL_COMANDOS_ID, REDIS_URL
import redis

class OverrideGoViral(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(
        name="override_go_viral",
        description="Permite que un usuario publique en go-viral sin restricciones (solo una vez)."
    )
    @app_commands.describe(usuario="Usuario que recibirá el override")
    async def override_go_viral(self, interaction: discord.Interaction, usuario: discord.Member):
        # Solo admin o mod puede usarlo
        if not (
            interaction.user.guild_permissions.administrator
            or str(interaction.user.id) == str(ADMIN_ID)
        ):
            await interaction.response.send_message(
                "❌ Solo administradores o moderadores pueden usar este comando.",
                ephemeral=True
            )
            return

        # Registrar override en Redis
        self.redis.set(f"go_viral:override:{usuario.id}", "1")

        await interaction.response.send_message(
            f"✅ Se ha otorgado **override** a {usuario.mention}. Podrá publicar en 🧵go-viral sin restricciones la próxima vez.",
            ephemeral=True
        )

        # Intentar notificar al usuario por DM
        try:
            await usuario.send("🚀 Un administrador te ha dado permiso especial para publicar en **🧵go-viral** sin restricciones. ¡Aprovéchalo!")
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(OverrideGoViral(bot))
