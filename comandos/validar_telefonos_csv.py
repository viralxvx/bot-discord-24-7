# comandos/validar_telefonos_csv.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import csv
import tempfile
import phonenumbers
import time
from utils.logger import custom_log
from utils.progreso import generar_barra_progreso
from utils.gofile import subir_a_gofile

class ValidarTelefonosCSV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="validar_telefonos_csv", description="Valida y corrige teléfonos de un archivo CSV")
    @app_commands.describe(pais="Código de país opcional (ej. RD, MX, US)")
    async def validar_telefonos_csv(self, interaction: discord.Interaction, pais: str = "RD"):
        await interaction.response.send_message("📥 Esperando archivo CSV para validar teléfonos...", ephemeral=True)
        await interaction.followup.send(content="⬆️ Por favor sube un archivo CSV...")

        def check(m):
            return m.author.id == interaction.user.id and m.attachments

        try:
            mensaje = await self.bot.wait_for("message", check=check, timeout=60)
            archivo = mensaje.attachments[0]
            if not archivo.filename.endswith(".csv"):
                await interaction.followup.send("❌ Por favor sube un archivo CSV válido.")
                return

            await interaction.followup.send(f"📤 Descargando {archivo.filename}...")
            archivo_bytes = await archivo.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_in:
                temp_in.write(archivo_bytes)
                ruta_entrada = temp_in.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_out:
                ruta_salida = temp_out.name

            contactos = []
            telefonos_unicos = set()
            with open(ruta_entrada, "r", encoding="utf-8") as f_in:
                reader = csv.DictReader(f_in)
                filas = list(reader)
                total = len(filas)

                mensaje_estado = await mensaje.channel.send("📊 Validando teléfonos...")

                for i, fila in enumerate(filas):
                    nombre = fila.get("Nombre", "").strip()
                    apellido = fila.get("Apellido", "").strip()
                    telefono = fila.get("Teléfono", "").strip()
                    correo = fila.get("Correo", "").strip()

                    try:
                        num = phonenumbers.parse(telefono, pais)
                        if phonenumbers.is_valid_number(num):
                            numero_formateado = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
                            if numero_formateado not in telefonos_unicos:
                                contactos.append({
                                    "Nombre": nombre,
                                    "Apellido": apellido,
                                    "Correo": correo,
                                    "Teléfono": numero_formateado
                                })
                                telefonos_unicos.add(numero_formateado)
                    except Exception:
                        pass

                    if i % 10 == 0 or i == total - 1:
                        progreso = int((i+1)/total * 100)
                        barra = generar_barra_progreso(progreso)
                        faltan = int(((total - i - 1) * 0.2))
                        tiempo_str = f"{faltan}s" if faltan < 60 else f"{faltan//60}m"
                        await mensaje_estado.edit(content=f"[Activo] ✅ Progreso: {barra} {progreso}% | ⏳ Faltan: {tiempo_str}")

            campos = ["Nombre", "Apellido", "Correo", "Teléfono"]
            with open(ruta_salida, "w", newline="", encoding="utf-8") as f_out:
                writer = csv.DictWriter(f_out, fieldnames=campos)
                writer.writeheader()
                writer.writerows(contactos)

            url = subir_a_gofile(ruta_salida)

            embed = discord.Embed(title="📑 Teléfonos validados con éxito", color=0x2ecc71)
            embed.add_field(name="Contactos válidos", value=str(len(contactos)), inline=True)
            embed.add_field(name="Archivo CSV", value=f"[Descargar CSV]({url})", inline=False)
            await mensaje_estado.edit(content=None, embed=embed)

            custom_log(self.bot, "VALIDAR_CSV", "INFO", f"Archivo validado y cargado a gofile: {url}")

        except Exception as e:
            await interaction.followup.send(f"❌ Error al validar CSV: {e}")
            custom_log(self.bot, "VALIDAR_CSV", "ERROR", str(e))

async def setup(bot):
    await bot.add_cog(ValidarTelefonosCSV(bot))
