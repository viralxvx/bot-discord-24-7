import discord
from discord.ext import commands
import re
import asyncio
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_OBJETIVO # CANAL_OBJETIVO es esencial aquí

# Definimos una clase Cog para organizar las funciones del canal Go-Viral
class GoViralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis_state = RedisState() # Instancia de RedisState

    # Este será tu "on_ready" para este módulo, pero con un nombre diferente
    # para evitar conflictos y llamarlo explícitamente desde main.py
    async def go_viral_on_ready(self):
        print(f"Lógica on_ready de GoViralCog iniciada para el canal {CANAL_OBJETIVO}...")

        # --- MODIFICACIÓN TEMPORAL AQUÍ ---
        # Comenta la siguiente línea para forzar el envío del mensaje de bienvenida
        # if not self.redis_state.is_welcome_message_active(CANAL_OBJETIVO):
        
        # Deja la siguiente línea sin comentar para que el código dentro del if siempre se ejecute
        # Esto es solo para probar. Luego, ¡recuerda descomentar la línea de arriba!
        if True: # <--- CAMBIA ESTO TEMPORALMENTE A 'if True:'
            print(f"DEBUG: Forzando el envío del mensaje de bienvenida (Redis check bypass).") # Mensaje de depuración
            channel_go_viral = self.bot.get_channel(CANAL_OBJETIVO)
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
                image_url = "https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj"
                embed = discord.Embed(title="🧵 REGLAS DEL CANAL GO-VIRAL 🧵", description=welcome_message, color=discord.Color.gold())
                embed.set_image(url=image_url)
                try:
                    sent_message = await channel_go_viral.send(embed=embed)
                    self.redis_state.set_welcome_message_id(sent_message.id, CANAL_OBJETIVO)
                    print("Mensaje de bienvenida al canal go-viral enviado exitosamente desde GoViralCog.")
                    await registrar_log("Mensaje de bienvenida enviado al canal go-viral", self.bot.user, channel_go_viral, self.bot)
                except discord.Forbidden:
                    print(f"ERROR: No tengo permisos para enviar el embed en el canal '{channel_go_viral.name}'.")
                except Exception as e:
                    print(f"ERROR al enviar el mensaje de bienvenida al canal '{channel_go_viral.name}': {e}")
            else:
                print(f"ERROR: No se pudo encontrar el canal go-viral con la ID: {CANAL_OBJETIVO}")
        # --- FIN DE LA MODIFICACIÓN TEMPORAL ---
        else: # Este else se ejecutará si la línea comentada arriba no está comentada y Redis dice que ya está activo
            print(f"Mensaje de bienvenida ya activo para el canal {CANAL_OBJETIVO} según Redis. No se envía de nuevo.")


    # Ahora, tus eventos on_message y on_reaction_add se convierten en métodos de la Cog
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
            await self.bot.process_commands(message)
            return

        redis_state = self.redis_state

        # Validar formato de la URL
        url_pattern = r'^https://x\.com/\w+/status/\d+$'
        content = message.content.strip()
        corrected_url = None
        if not re.match(url_pattern, content):
            try:
                base_url = re.match(r'(https://x\.com/\w+/status/\d+)', content).group(1)
                corrected_url = base_url
            except AttributeError:
                await message.delete()
                await enviar_notificacion_temporal(message.channel, message.author,
                    f"{message.author.mention} **Error:** La URL no es válida. Usa el formato: `https://x.com/usuario/status/123456...`")
                await registrar_falta(message.author, "URL inválida", message.channel)
                await registrar_log("Mensaje eliminado: URL inválida", message.author, message.channel, self.bot)
                return

        # Verificar intervalo de publicaciones
        last_post = redis_state.get_last_post(message.author.id)
        recent_posts = redis_state.get_recent_posts(CANAL_OBJETIVO)
        if last_post and len([p for p in recent_posts if p['author_id'] != message.author.id]) < 2:
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **Error:** Debes esperar al menos 2 publicaciones válidas de otros usuarios antes de publicar nuevamente.")
            await registrar_falta(message.author, "Publicación antes de intervalo permitido", message.channel)
            await registrar_log("Mensaje eliminado: Intervalo no respetado", message.author, message.channel, self.bot)
            return

        # Verificar reacciones 🔥 en publicaciones previas
        required_reactions = redis_state.get_required_reactions(message.author.id, CANAL_OBJETIVO)
        if not all(redis_state.has_reaction(message.author.id, post_id) for post_id in required_reactions):
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **Error:** Debes reaccionar con 🔥 a todas las publicaciones posteriores a tu última publicación.")
            await registrar_falta(message.author, "Falta de reacciones 🔥", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacciones 🔥", message.author, message.channel, self.bot)
            return

        # Corregir URL si es necesario
        if corrected_url:
            await message.delete()
            new_message = await message.channel.send(f"{corrected_url} (Corregido por el bot)")
            await registrar_log(f"URL corregida: {content} -> {corrected_url}", message.author, message.channel, self.bot)
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **URL corregida:** Usa el formato `https://x.com/usuario/status/123456...` sin parámetros adicionales.")
            message = new_message

        # Guardar publicación en Redis
        redis_state.save_post(message.id, message.author.id, CANAL_OBJETIVO)
        await registrar_log("Nueva publicación válida registrada", message.author, message.channel, self.bot)

        # Esperar reacción 👍 del autor
        def check_reaction(reaction, user_check):
            return user_check == message.author and str(reaction.emoji) == '👍' and reaction.message.id == message.id

        try:
            await self.bot.wait_for('reaction_add', timeout=120, check=check_reaction)
            print(f"Reacción 👍 del autor detectada para el mensaje {message.id}")
        except asyncio.TimeoutError:
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **Error:** No reaccionaste con 👍 a tu publicación en 120 segundos.")
            await registrar_falta(message.author, "Sin reacción 👍 en 120 segundos", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacción 👍", message.author, message.channel, self.bot)
            return

        await self.bot.process_commands(message)


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.channel.id != CANAL_OBJETIVO or user.bot:
            return

        # Prohibir 🔥 en propia publicación
        if str(reaction.emoji) == '🔥' and user == reaction.message.author:
            try:
                await reaction.remove(user)
                print(f"Reacción 🔥 eliminada de la propia publicación de {user.name}")
            except discord.Forbidden:
                print(f"Error: No se pudo eliminar la reacción 🔥 de {user.name} (permisos).")
            await enviar_notificacion_temporal(reaction.message.channel, user,
                f"{user.mention} **Error:** No puedes reaccionar con 🔥 a tu propia publicación.")
            await registrar_falta(user, "Reacción 🔥 en propia publicación", reaction.message.channel)
            await registrar_log("Reacción eliminada: 🔥 en propia publicación", user, reaction.message.channel, self.bot)
            return

        # Registrar reacción 🔥 válida
        if str(reaction.emoji) == '🔥' and user != reaction.message.author:
            self.redis_state.save_reaction(user.id, reaction.message.id)
            print(f"Reacción 🔥 de {user.name} registrada para el mensaje {reaction.message.id}")


# La función setup ahora añade la Cog al bot
def setup(bot):
    bot.add_cog(GoViralCog(bot))

# Las funciones auxiliares pueden ir aquí, ya que no son parte de la Cog directamente
# o podrían ser métodos estáticos de la Cog si no necesitan 'self'
async def enviar_notificacion_temporal(channel, user, content):
    msg = await channel.send(content)
    await asyncio.sleep(15)
    await msg.delete()
    try:
        await user.send(f"⚠️ **Notificación de {channel.name}**: {content.replace(user.mention, '')}\n\n*Este es un mensaje automático del bot.*")
    except discord.Forbidden:
        print(f"Error: No se pudo enviar DM a {user.name}. Puede que tenga los DMs deshabilitados.")
