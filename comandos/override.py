import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ID, CANAL_COMANDOS_ID, REDIS_URL
import redis
from utils.logger import log_discord

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
        # Solo admin puede usarlo y SOLO en el canal de comandos
        if not (
            interaction.user.guild_permissions.administrator
            or str(interaction.user.id) == str(ADMIN_ID)
        ):
            await interaction.response.send_message(
                "❌ Solo administradores pueden usar este comando.",
                ephemeral=True
            )
            return

        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                f"❌ Usa este comando SOLO en el canal correcto (<#{CANAL_COMANDOS_ID}>).",
                ephemeral=True
            )
            return

        if usuario.bot:
            await interaction.response.send_message(
                "❌ No puedes dar override a un bot.",
                ephemeral=True
            )
            return

        key = f"go_viral:override:{usuario.id}"
        if self.redis.get(key) == "1":
            await interaction.response.send_message(
                f"⚠️ {usuario.mention} ya tenía override activo.",
                ephemeral=True
            )
            return

        # Registrar override
        self.redis.set(key, "1")
        await interaction.response.send_message(
            f"✅ Se ha otorgado **override** a {usuario.mention}. Podrá publicar en 🧵go-viral sin restricciones la próxima vez.",
            ephemeral=True
        )

        # Auditar uso
        await log_discord(self.bot, f"{interaction.user.mention} otorgó override a {usuario.mention} en go-viral.", "info", "Override go-viral")

        # Notificar por DM
        try:
            await usuario.send("🚀 Un administrador te ha dado permiso especial para publicar en **🧵go-viral** sin restricciones. ¡Aprovéchalo! (Solo funciona para un post).")
        except Exception:
            pass

    @app_commands.command(
        name="quitar_override_go_viral",
        description="Revoca el permiso especial de override para un usuario en go-viral."
    )
    @app_commands.describe(usuario="Usuario al que quitar el override")
    async def quitar_override_go_viral(self, interaction: discord.Interaction, usuario: discord.Member):
        # Solo admin y solo canal de comandos
        if not (
            interaction.user.guild_permissions.administrator
            or str(interaction.user.id) == str(ADMIN_ID)
        ):
            await interaction.response.send_message(
                "❌ Solo administradores pueden usar este comando.",
                ephemeral=True
            )
            return

        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                f"❌ Usa este comando SOLO en el canal correcto (<#{CANAL_COMANDOS_ID}>).",
                ephemeral=True
            )
            return

        key = f"go_viral:override:{usuario.id}"
        if not self.redis.exists(key):
            await interaction.response.send_message(
                f"⚠️ {usuario.mention} no tenía override activo.",
                ephemeral=True
            )
            return

        self.redis.delete(key)
        await interaction.response.send_message(
            f"🗑️ Se ha removido el override de {usuario.mention}. Ahora debe cumplir las reglas normales de go-viral.",
            ephemeral=True
        )
        await log_discord(self.bot, f"{interaction.user.mention} revocó override a {usuario.mention} en go-viral.", "info", "Override go-viral")

    @app_commands.command(
        name="listar_overrides_go_viral",
        description="Muestra la lista de usuarios con override activo para go-viral."
    )
    async def listar_overrides_go_viral(self, interaction: discord.Interaction):
        # Solo admin y solo canal de comandos
        if not (
            interaction.user.guild_permissions.administrator
            or str(interaction.user.id) == str(ADMIN_ID)
        ):
            await interaction.response.send_message(
                "❌ Solo administradores pueden usar este comando.",
                ephemeral=True
            )
            return

        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                f"❌ Usa este comando SOLO en el canal correcto (<#{CANAL_COMANDOS_ID}>).",
                ephemeral=True
            )
            return

        # Buscar overrides en Redis
        overrides = [k for k in self.redis.scan_iter("go_viral:override:*") if self.redis.get(k) == "1"]
        if not overrides:
            await interaction.response.send_message(
                "Actualmente no hay ningún usuario con override activo para go-viral.",
                ephemeral=True
            )
            return

        # Buscar miembros y preparar la lista
        ids = [int(k.split(":")[-1]) for k in overrides]
        miembros = []
        for uid in ids:
            miembro = interaction.guild.get_member(uid)
            if miembro:
                miembros.append(f"{miembro.mention} (`{uid}`)")
            else:
                miembros.append(f"`{uid}` (No encontrado en el servidor)")

        embed = discord.Embed(
            title="👤 Lista de overrides activos en 🧵go-viral",
            description="\n".join(miembros),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(OverrideGoViral(bot))
