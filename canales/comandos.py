# canales/comandos.py

import discord
from discord.ext import commands
import os
import asyncio
from config import CANAL_COMANDOS_ID
from mensajes.comandos_texto import INSTRUCCIONES_COMANDOS, INSTRUCCIONES_SUGERENCIAS

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
            await canal.purge(limit=50)
            print("✅ Canal de comandos limpio.")

            # Verificar mensajes existentes
            mensajes_actuales = [msg async for msg in canal.history(limit=20)]

            # Enviar instrucciones generales si no existen
            if not any(msg.content == INSTRUCCIONES_COMANDOS for msg in mensajes_actuales):
                await self.enviar_mensaje_con_reintento(canal, INSTRUCCIONES_COMANDOS)
                print("📌 Instrucciones generales enviadas.")
            else:
                print("📌 Las instrucciones generales ya están presentes.")

            # Enviar instrucciones de sugerencias si no existen
            if not any(msg.content == INSTRUCCIONES_SUGERENCIAS for msg in mensajes_actuales):
                await self.enviar_mensaje_con_reintento(canal, INSTRUCCIONES_SUGERENCIAS)
                print("📌 Instrucciones de sugerencias enviadas.")
            else:
                print("📌 Las instrucciones de sugerencias ya están presentes.")

        except Exception as e:
            print(f"❌ Error al configurar el canal de comandos: {e}")

    async def enviar_mensaje_con_reintento(self, canal, mensaje):
        for intento in range(5):
            try:
                await canal.send(mensaje)
                return
            except discord.errors.HTTPException as e:
                if e.code == 429:
                    wait_time = 2 ** intento
                    print(f"⏳ Rate limit detectado. Esperando {wait_time} segundos...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Error inesperado al enviar mensaje: {e}")
                    break

async def setup(bot):
    await bot.add_cog(CanalComandos(bot))
