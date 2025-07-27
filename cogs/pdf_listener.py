# cogs/pdf_listener.py
import discord
from discord.ext import commands
import fitz
import time
import os
from utils.pdf_parser import extraer_contactos_desde_pdf
from utils.redis_conn import redis_conn
from utils.logger import custom_log

CANAL_IMPORTAR_PDF = os.getenv("CANAL_IMPORTAR_PDF")

class PDFListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if str(message.channel.id) != CANAL_IMPORTAR_PDF:
            return

        if not message.attachments:
            return

        pdf = next((a for a in message.attachments if a.filename.endswith(".pdf")), None)
        if not pdf:
            return

        archivo_nombre = pdf.filename
        archivo_path = f"/tmp/{archivo_nombre}"
        await pdf.save(archivo_path)

        canal = message.channel
        progreso_msg = await canal.send(f"⏳ Procesando archivo: `{archivo_nombre}`...")

        doc = fitz.open(archivo_path)
        total_paginas = len(doc)
        tiempo_inicio = time.time()
        fotos_detectadas = 0

        def formato_tiempo(segundos):
            if segundos >= 3600:
                return f"{segundos // 3600}h {(segundos % 3600) // 60}m"
            elif segundos >= 60:
                return f"{segundos // 60}m {segundos % 60}s"
            else:
                return f"{segundos}s"

        async def actualizar_progreso(pagina_actual, total_paginas, porcentaje, faltan):
            nonlocal fotos_detectadas
            try:
                pagina = doc[pagina_actual - 1]
                fotos_detectadas += len(pagina.get_images(full=True))
            except:
                pass

            bloques = 10
            llenos = int((porcentaje / 100) * bloques)
            vacios = bloques - llenos
            barra = "█" * llenos + "░" * vacios
            tiempo_legible = formato_tiempo(faltan)
            msg = f"📄 Página {pagina_actual}/{total_paginas} | {porcentaje}% [{barra}] ⏳ Tiempo estimado: {tiempo_legible}"
            await progreso_msg.edit(content=msg)

        try:
            contactos = await extraer_contactos_desde_pdf(
                archivo_path,
                user_id=message.author.id,
                progreso_callback=actualizar_progreso
            )

            if contactos:
                clave = f"pdf:{message.id}:{archivo_nombre}:contactos"
                redis_conn.set(clave, str(contactos), ex=3600)
                await progreso_msg.edit(content=f"✅ PDF procesado: {len(contactos)} contactos detectados.")
            else:
                await progreso_msg.edit(content="⚠️ No se encontraron contactos en el PDF.")

        except Exception as e:
            await progreso_msg.edit(content=f"❌ Error al procesar PDF desde mensaje: {e}")
            custom_log(self.bot, "PDFListener", "ERROR", f"Error procesando PDF: {e}")

async def setup(bot):
    await bot.add_cog(PDFListener(bot))
