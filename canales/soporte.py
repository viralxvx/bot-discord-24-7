import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Modal, TextInput
from config import CANAL_SOPORTE_ID, REDIS_URL
from mensajes.soporte_mensajes import MENSAJE_INTRO, OPCIONES_MENU, EXPLICACIONES
from mensajes.inactividad_texto import PRORROGA_CONCEDIDA
from utils.logger import log_discord
from datetime import datetime, timedelta, timezone
import redis
import json

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class MenuSoporteView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuSoporteSelect())

class MenuSoporteSelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Selecciona una opción para obtener ayuda...",
            options=OPCIONES_MENU
        )

    async def callback(self, interaction: discord.Interaction):
        opcion = self.values[0]
        contenido = EXPLICACIONES.get(opcion)

        if not contenido:
            await interaction.response.send_message("❌ Esta opción aún no está disponible.", ephemeral=True)
            return

        await interaction.response.send_message(embed=contenido, ephemeral=True)

        if opcion == "sugerencia":
            modal = SugerenciaModal()
            await interaction.response.send_modal(modal)

class SugerenciaModal(Modal, title="📫 Enviar una sugerencia"):
    sugerencia = TextInput(label="¿Cuál es tu sugerencia?", style=discord.TextStyle.paragraph, required=True)
    usuario = TextInput(label="Tu usuario (opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        contenido = {
            "autor_id": str(interaction.user.id),
            "usuario_visible": self.usuario.value or "Anónimo",
            "sugerencia": self.sugerencia.value
        }

        clave = f"sugerencia:{interaction.user.id}:{interaction.id}"
        redis_client.set(clave, json.dumps(contenido))

        await interaction.response.send_message("✅ ¡Gracias por tu sugerencia! La hemos guardado correctamente.", ephemeral=True)

class Soporte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def iniciar_soporte(self):
        canal = self.bot.get_channel(CANAL_SOPORTE_ID)
        print(f"[DEBUG] Canal detectado: {canal}")

        if not canal:
            await log_discord(self.bot, "Error", "No se encontró el canal de soporte.", "❌ Error soporte")
            return

        try:
            mensajes_fijados = await canal.pins()
            print(f"[DEBUG] Pins encontrados: {len(mensajes_fijados)}")
        except Exception as e:
            await log_discord(self.bot, "Error", f"No se pudieron obtener los mensajes fijados: {e}", "❌ Error pins")
            return

        mensaje_bot = None
        for m in mensajes_fijados:
            if m.author == self.bot.user and m.embeds:
                if m.embeds[0].title == MENSAJE_INTRO.title:
                    mensaje_bot = m
                    break

        if mensaje_bot:
            print("[DEBUG] Mensaje de soporte detectado. Editando.")
            await mensaje_bot.edit(embed=MENSAJE_INTRO, view=MenuSoporteView())
        else:
            print("[DEBUG] No se encontró mensaje válido. Creando nuevo mensaje de soporte.")
            nuevo_mensaje = await canal.send(embed=MENSAJE_INTRO, view=MenuSoporteView())
            await nuevo_mensaje.pin()
            print("📌 Mensaje de soporte creado y fijado.")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.iniciar_soporte()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.id != CANAL_SOPORTE_ID:
            return

        member = message.author

        if not (member.guild_permissions.administrator or member.guild_permissions.manage_guild):
            key_prorroga = f"inactividad:prorroga:{member.id}"
            ahora = datetime.now(timezone.utc)
            prorroga_actual = redis_client.get(key_prorroga)

            if prorroga_actual:
                fecha_prorroga = datetime.fromisoformat(prorroga_actual)
                if ahora < fecha_prorroga:
                    try:
                        await message.reply(
                            "⏳ Ya tienes una prórroga activa. Espera a que termine antes de solicitar otra.",
                            mention_author=False
                        )
                    except Exception:
                        pass
                    try:
                        await message.delete()
                    except:
                        pass
                    return

            dias = 7
            hasta = ahora + timedelta(days=dias)
            redis_client.set(key_prorroga, hasta.isoformat())

            try:
                await member.send(PRORROGA_CONCEDIDA.format(dias=dias))
            except Exception as e:
                print(f"⚠️ [PRÓRROGA] No se pudo enviar DM a {member.display_name}: {e}")

            try:
                await message.channel.send(
                    f"✅ {member.mention}, tu prórroga de {dias} días fue registrada. Revisa tu DM.",
                    delete_after=10
                )
            except:
                pass

        try:
            await message.delete()
        except:
            pass

        try:
            await member.send(
                "📌 Este canal es exclusivo para el soporte automatizado de VX.\n"
                "Usa el mensaje fijado para enviar sugerencias o recibir ayuda."
            )
        except:
            pass

async def setup(bot):
    await bot.add_cog(Soporte(bot))
