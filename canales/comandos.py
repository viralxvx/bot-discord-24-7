import discord
from discord.ext import commands
import os
from config import CANAL_COMANDOS_ID
from mensajes.comandos_texto import INSTRUCCIONES_COMANDOS
import asyncio

class CanalComandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.configurar_canal())

    async def configurar_canal(self):
        await self.bot.wait_until_ready()
        print("⚙️ Iniciando módulo del canal de comandos...")

        canal = self.bot.get_channel(CANAL_COMANDOS_ID)
        if not canal:
            print("❌ Error: no se encontró el canal de comandos.")
            return

        try:
            print("🧹 Limpiando mensajes antiguos del canal de comandos...")

            # Limitar la cantidad de mensajes que se eliminan por vez para evitar rate limit
            await canal.purge(limit=50)  # Limita a borrar 50 mensajes por vez
            print("✅ Canal de comandos limpio.")

            # Verificar si el mensaje de instrucciones ya fue enviado
            mensajes = [msg async for msg in canal.history(limit=10)]
            if not any(msg.content == INSTRUCCIONES_COMANDOS for msg in mensajes):
                # Si no hay un mensaje con las instrucciones, enviamos uno nuevo
                await self.enviar_mensaje_con_reintento(canal, INSTRUCCIONES_COMANDOS)
                print("📌 Instrucciones de uso enviadas.")
            else:
                print("📌 Las instrucciones ya están enviadas en el canal de comandos.")
        except Exception as e:
            print(f"❌ Error al configurar el canal de comandos: {e}")

    async def enviar_mensaje_con_reintento(self, canal, mensaje):
        # Intentamos enviar el mensaje varias veces en caso de rate limiting
        for intento in range(5):  # Intentar hasta 5 veces
            try:
                await canal.send(mensaje)
                return  # Si el mensaje se envía correctamente, salimos
            except discord.errors.HTTPException as e:
                if e.code == 429:  # Si el error es rate limiting (429)
                    wait_time = 2 ** intento  # Exponential backoff
                    print(f"Rate limiting detectado. Esperando {wait_time} segundos...")
                    await asyncio.sleep(wait_time)  # Esperamos antes de reintentar
                else:
                    # Si es otro error, lo registramos y salimos
                    print(f"Error inesperado al enviar mensaje: {e}")
                    break

# 👉 Formato asincrónico requerido por discord.py 2.0+
async def setup(bot):
    await bot.add_cog(CanalComandos(bot))
