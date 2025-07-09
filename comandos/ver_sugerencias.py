import discord
from discord import app_commands
from discord.ext import commands
import redis
from config import REDIS_URL, CANAL_COMANDOS_ID

class VerSugerencias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    @app_commands.command(name="ver_sugerencias", description="📬 Revisa las sugerencias enviadas por los usuarios (solo admins).")
    async def ver_sugerencias(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_COMANDOS_ID:
            await interaction.response.send_message(
                "❌ Este comando solo puede usarse en el canal 💻comandos.",
                ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🔒 Este comando es solo para administradores.",
                ephemeral=True
            )
            return

        claves = self.redis.keys("sugerencia:*")
        if not claves:
            await interaction.response.send_message("📭 No hay sugerencias guardadas aún.", ephemeral=True)
            return

        sugerencias = []
        for clave in claves:
            data = self.redis.hgetall(clave)
            estado = data.get("estado", "pendiente").capitalize()
            texto = data.get("contenido", "Sin contenido")
            autor_id = clave.split(":")[1]
            sugerencias.append((autor_id, texto, estado))

        embeds = []
        for autor_id, texto, estado in sugerencias:
            user = await self.bot.fetch_user(int(autor_id))
            embed = discord.Embed(
                title=f"📨 Sugerencia de {user.name}",
                description=texto,
                color=discord.Color.blurple()
            )
            embed.add_field(name="Estado", value=estado)
            embed.set_footer(text=f"Usuario ID: {autor_id}")
            embeds.append(embed)

        await interaction.response.send_message(embeds=embeds[:10], ephemeral=True)  # Muestra hasta 10 sugerencias

async def setup(bot):
    print("[DEBUG] Cargando cog VerSugerencias...")
    await bot.add_cog(VerSugerencias(bot))
    print("[DEBUG] VerSugerencias registrado correctamente.")
