import discord
from discord import app_commands
from discord.ext import commands
from config import CANAL_COMANDOS_ID, ADMIN_ID
from mensajes.comandos_texto import generar_embed_estado
import logging

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="estado", description="Consulta tu estado actual en el sistema de faltas.")
    async def estado(self, interaction: discord.Interaction):
        user = interaction.user
        canal_origen = interaction.channel

        logging.info(f"[COMANDO /estado] Ejecutado por {user} (ID: {user.id}) en canal {canal_origen.id}")

        # Verificar que se ejecute solo en el canal correcto
        if canal_origen.id != CANAL_COMANDOS_ID:
            logging.warning("❌ Comando /estado ejecutado fuera del canal permitido.")
            await interaction.response.send_message("❌ Este comando solo se puede usar en el canal 💻comandos.", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=False)  # Permite esperar más de 3s

            logging.info("✅ Generando embed de estado...")
            embed = await generar_embed_estado(user)

            logging.info("📤 Enviando embed en canal...")
            mensaje = await canal_origen.send(embed=embed, delete_after=600)  # se borra en 10 minutos

            logging.info("📬 Enviando embed por DM...")
            await user.send(embed=embed)

        except Exception as e:
            logging.error(f"❌ Error en /estado: {e}")
            try:
                await interaction.followup.send("❌ Hubo un error al procesar tu estado. Contacta a un moderador.", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Estado(bot))
