import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, CANAL_OBJETIVO, CANAL_LOGS # Importa las IDs de los canales
from canales.go_viral import setup as go_viral_setup
from canales.logs import registrar_log # Importa tu función de logs
from state_management import RedisState # Necesitas esto para el estado del mensaje de bienvenida

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True # Asegúrate de tener este intent también si usas guild.get_channel

bot = commands.Bot(command_prefix='!', intents=intents)

# Registra los eventos y comandos de 'go_viral' EXCEPTO su on_ready
go_viral_setup(bot)

@bot.event
async def on_ready():
    # Espera a que el bot esté completamente listo y la caché cargada
    await bot.wait_until_ready()
    print(f'Bot conectado como {bot.user}')

    # --- Lógica de envío al canal de logs ---
    canal_logs = bot.get_channel(CANAL_LOGS)
    if canal_logs:
        try:
            await canal_logs.send(f"🟢 **Bot conectado como `{bot.user.name}` y listo para funcionar.**")
            print("Mensaje de conexión enviado al canal de logs.")
        except Exception as e:
            print(f"Error al enviar mensaje al canal de logs: {e}")
    else:
        print(f"Error: Canal de logs con ID {CANAL_LOGS} no encontrado.")

    # --- Lógica para enviar el mensaje de bienvenida al CANAL_OBJETIVO ---
    # Usaremos Redis para saber si el mensaje ya fue enviado en las últimas 24 horas
    redis_state = RedisState()
    
    if not redis_state.is_welcome_message_active(CANAL_OBJETIVO):
        print(f"No hay un mensaje de bienvenida activo en Redis para el canal {CANAL_OBJETIVO}. Procediendo a enviar.")
        channel_go_viral = bot.get_channel(CANAL_OBJETIVO)
        if channel_go_viral:
            welcome_message = """
# 🧵 **REGLAS DEL CANAL GO-VIRAL** 🧵
## 🎉 **¡BIENVENIDOS A GO-VIRAL!** 🎉
¡Nos alegra tenerte aquí! Este es tu espacio para hacer crecer tu contenido de **𝕏 (Twitter)** junto a nuestra increíble comunidad.
## 🎯 **OBJETIVO**
Compartir contenido de calidad de **𝕏 (Twitter)** siguiendo un sistema organizado de apoyo mutuo.
---
## 📋 **REGLAS PRINCIPALES**
### 🔗 **1. FORMATO DE PUBLICACIÓN**
✅ **FORMATO CORRECTO:**
https://x.com/miguelrperaltaf/status/1931928250735026238
❌ **FORMATO INCORRECTO:**
https://x.com/miguelrperaltaf/status/1931928250735026238?s=46&t=m7qBPHFiZFqks3K1jSaVJg

**📝 NOTA:** El bot corregirá automáticamente los enlaces mal formateados, pero es mejor aprender el formato correcto.
### 👍 **2. VALIDACIÓN DE TU POST**
- Reacciona con **👍** a tu propia publicación
- **⏱️ Tiempo límite:** 120 segundos
- Sin reacción = eliminación automática
### 🔥 **3. APOYO A LA COMUNIDAD**
Antes de publicar nuevamente:
- Reacciona con **🔥** a TODAS las publicaciones posteriores a tuya
- **REQUISITO:** Apoya primero en **𝕏** con RT + LIKE + COMENTARIO
- Luego reacciona con 🔥 en Discord
### ⏳ **4. INTERVALO ENTRE PUBLICACIONES**
- Espera mínimo **2 publicaciones válidas** de otros usuarios
- No hay límite de tiempo, solo orden de turnos
---
## ⚠️ **SISTEMA DE FALTAS**
### 🚨 **Infracciones que generan falta:**
- Formato incorrecto de URL
- No reaccionar con 👍 a tiempo
- Publicar sin haber apoyado posts anteriores
- Usar 🔥 en tu propia publicación
- No respetar el intervalo de publicaciones
### 📊 **Consecuencias:**
- Registro en canal de faltas
- Notificación por DM
- Posibles sanciones según historial
---
## 🤖 **AUTOMATIZACIÓN DEL BOT**
- ✅ Corrección automática de URLs mal formateadas
- 🗑️ Eliminación de publicaciones inválidas
- 📬 Notificaciones temporales (15 segundos)
- 📝 Registro completo en logs
- 💬 Mensajes privados informativos
---
## 🏆 **CONSEJOS PARA EL ÉXITO**
1. **Lee las reglas** antes de participar
2. **Apoya genuinamente** en 𝕏 antes de reaccionar
3. **Mantén el formato** exacto de URLs
4. **Sé constante** con las reacciones
5. **Respeta los turnos** de otros usuarios
---
## 📞 **¿DUDAS?**
Revisa el historial del canal o consulta en el canal soporte.
**¡Juntos hacemos crecer nuestra comunidad! 🚀**
---
*Bot actualizado • Sistema automatizado • Apoyo 24/7*
"""
            image_url = "https://i.imgur.com/gK1S1e5.png" # Asegúrate de que esta URL sea real y válida
            embed = discord.Embed(title="🧵 REGLAS DEL CANAL GO-VIRAL 🧵", description=welcome_message, color=discord.Color.gold())
            embed.set_image(url=image_url)
            try:
                sent_message = await channel_go_viral.send(embed=embed)
                redis_state.set_welcome_message_id(sent_message.id, CANAL_OBJETIVO)
                print("Mensaje de bienvenida al canal go-viral enviado exitosamente.")
                await registrar_log("Mensaje de bienvenida enviado al canal go-viral", bot.user, channel_go_viral, bot)
            except discord.Forbidden:
                print(f"ERROR: No tengo permisos para enviar el embed en el canal '{channel_go_viral.name}'.")
            except Exception as e:
                print(f"ERROR al enviar el mensaje de bienvenida al canal '{channel_go_viral.name}': {e}")
        else:
            print(f"ERROR: No se pudo encontrar el canal go-viral con la ID: {CANAL_OBJETIVO}")
    else:
        print(f"Mensaje de bienvenida ya activo para el canal {CANAL_OBJETIVO} según Redis. No se envía de nuevo.")


async def main():
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
