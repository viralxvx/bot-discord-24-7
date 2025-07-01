import discord
from discord.ext import commands
import re
import asyncio
from state_management import RedisState # Asegúrate de que RedisState esté actualizado
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_OBJETIVO

class GoViralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis_state = RedisState()

    async def go_viral_on_ready(self):
        print(f"Lógica on_ready de GoViralCog iniciada para el canal {CANAL_OBJETIVO}...")

        if not self.redis_state.is_welcome_message_active(CANAL_OBJETIVO):
            print(f"DEBUG: Revisando Redis para mensaje de bienvenida para el canal {CANAL_OBJETIVO}.")
            channel_go_viral = self.bot.get_channel(CANAL_OBJETIVO)
            if channel_go_viral:
                welcome_message = """
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
        else:
            print(f"Mensaje de bienvenida ya activo para el canal {CANAL_OBJETIVO} según Redis. No se envía de nuevo.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
            await self.bot.process_commands(message)
            return

        redis_state = self.redis_state
        user_id_str = str(message.author.id)
        
        # Punto 6: Verificar si es el primer post del usuario
        is_first_post_ever = not redis_state.redis_client.exists(f"user_first_post:{user_id_str}")

        # ------------------------------------------------------------------------------------------------
        # Validación de formato de URL
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
        
        # ------------------------------------------------------------------------------------------------
        # Validación de intervalo de publicaciones (esperar 2 válidas de otros)
        last_post_time = redis_state.get_last_post_time(message.author.id)
        recent_posts_count_others = len([p for p in redis_state.get_recent_posts(CANAL_OBJETIVO) if str(p['author_id']) != user_id_str])

        if not is_first_post_ever: # Solo aplicamos la regla si no es el primer post del usuario
            if last_post_time and recent_posts_count_others < 2:
                await message.delete()
                await enviar_notificacion_temporal(message.channel, message.author,
                    f"{message.author.mention} **Error:** Debes esperar al menos 2 publicaciones válidas de otros usuarios antes de publicar nuevamente.")
                await registrar_falta(message.author, "Publicación antes de intervalo permitido", message.channel)
                await registrar_log("Mensaje eliminado: Intervalo no respetado", message.author, message.channel, self.bot)
                return

        # ------------------------------------------------------------------------------------------------
        # Punto 4: Validación de reacciones 🔥 en publicaciones previas
        if not is_first_post_ever: # Los usuarios nuevos no tienen que apoyar en su primera publicación
            required_reactions_details = redis_state.get_required_reactions_details(message.author.id, CANAL_OBJETIVO)
            missing_reactions = []
            
            for post_data in required_reactions_details:
                if not redis_state.has_reaction(message.author.id, post_data['message_id']):
                    missing_reactions.append(post_data)

            if missing_reactions:
                await message.delete()
                
                missing_info_list = []
                for mr in missing_reactions:
                    missing_info_list.append(f"- **{mr['author_name']}**: <{mr['url']}>") # Usamos <> para deshabilitar embeds en links

                missing_info_str = "\n".join(missing_info_list)

                channel_msg = (
                    f"{message.author.mention} **Error:** Debes reaccionar con 🔥 a las siguientes publicaciones antes de publicar:\n"
                    f"{missing_info_str}"
                )
                dm_msg = (
                    f"⚠️ **Tienes reacciones 🔥 pendientes en el canal {message.channel.name}**.\n"
                    f"Debes apoyar estas publicaciones en 𝕏 y reaccionar con 🔥 en Discord antes de volver a publicar:\n"
                    f"{missing_info_str}\n\n*Este es un mensaje automático del bot.*"
                )

                await enviar_notificacion_temporal(message.channel, message.author, channel_msg)
                try:
                    await message.author.send(dm_msg)
                except discord.Forbidden:
                    print(f"Error: No se pudo enviar DM a {message.author.name} (DMs deshabilitados).")

                await registrar_falta(message.author, "Falta de reacciones 🔥 pendientes", message.channel)
                await registrar_log(f"Mensaje eliminado: Sin reacciones 🔥 pendientes. Faltantes: {missing_info_str}", message.author, message.channel, self.bot)
                return
        
        # ------------------------------------------------------------------------------------------------
        # Punto 7: Corrección de URL automática (usando Webhook para mantener el autor original)
        final_message_content = corrected_url if corrected_url else content
        webhook_message = None # Para guardar la referencia del mensaje enviado por webhook

        try:
            # Obtener o crear el webhook
            webhook = await self.redis_state.get_or_create_webhook(message.channel)
            
            # Eliminar el mensaje original del usuario
            await message.delete()
            
            # Enviar el mensaje corregido o original a través del webhook
            # Aparecerá como si lo hubiera enviado el usuario original
            webhook_message = await webhook.send(
                content=final_message_content,
                username=message.author.display_name,
                avatar_url=message.author.display_avatar.url,
                wait=True # Esperar a que el webhook se envíe
            )
            
            # Si se corrigió el URL, enviar una notificación temporal al usuario
            if corrected_url:
                await enviar_notificacion_temporal(message.channel, message.author,
                    f"{message.author.mention} **¡Link corregido!** Tu publicación se ha ajustado al formato correcto. Por favor, recuerda usar `https://x.com/usuario/status/ID` sin parámetros adicionales para futuras publicaciones.")
                await registrar_log(f"URL corregida (via webhook): {content} -> {corrected_url}", message.author, message.channel, self.bot)
            
            # El mensaje que usamos para la validación de 👍 y para Redis será el de webhook.
            # Necesitamos el objeto de mensaje real, no solo la URL
            final_message = webhook_message 
            
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para gestionar webhooks o enviar via webhook en el canal '{message.channel.name}'.")
            # Fallback si no se puede usar webhook: el bot envía el mensaje
            final_message = await message.channel.send(f"{final_message_content} (Publicado por el bot debido a error de permisos/webhook)")
            if corrected_url:
                await enviar_notificacion_temporal(message.channel, message.author,
                    f"{message.author.mention} **¡Link corregido!** Tu publicación se ha ajustado al formato correcto. Por favor, recuerda usar `https://x.com/usuario/status/ID` sin parámetros adicionales para futuras publicaciones.")
                await registrar_log(f"URL corregida (fallback bot): {content} -> {corrected_url}", message.author, message.channel, self.bot)

        except Exception as e:
            print(f"ERROR al enviar mensaje via webhook o gestionar: {e}")
            # Fallback en caso de cualquier otro error con webhook
            final_message = await message.channel.send(f"{final_message_content} (Publicado por el bot debido a un error)")
            if corrected_url:
                await enviar_notificacion_temporal(message.channel, message.author,
                    f"{message.author.mention} **¡Link corregido!** Tu publicación se ha ajustado al formato correcto. Por favor, recuerda usar `https://x.com/usuario/status/ID` sin parámetros adicionales para futuras publicaciones.")
                await registrar_log(f"URL corregida (fallback bot): {content} -> {corrected_url}", message.author, message.channel, self.bot)


        # ------------------------------------------------------------------------------------------------
        # Guardar publicación en Redis (usando el message_id del webhook_message si fue usado)
        # Esto es importante para que el post pueda ser "esperado" por otros usuarios para sus 🔥 reacciones.
        self.redis_state.save_post(final_message.id, final_message.author.id, CANAL_OBJETIVO, final_message.content, final_message.author.name)
        await registrar_log("Nueva publicación válida registrada (pendiente de 👍)", final_message.author, final_message.channel, self.bot)

        # ------------------------------------------------------------------------------------------------
        # Punto 1, 2, 3, 5: Esperar reacción 👍 del autor
        def check_reaction(reaction, user_check):
            # Depuración y reconocimiento
            print(f"DEBUG REACTION CHECK: Reaction emoji: {str(reaction.emoji)}, User ID: {user_check.id} ({user_check.name}), Message ID: {reaction.message.id}")
            print(f"DEBUG REACTION CHECK: Expected user ID: {final_message.author.id}, Expected message ID: {final_message.id}")
            return user_check == final_message.author and str(reaction.emoji) == '👍' and reaction.message.id == final_message.id

        try:
            print(f"DEBUG: Esperando reacción 👍 para mensaje {final_message.id} por {final_message.author.name}...")
            await self.bot.wait_for('reaction_add', timeout=120, check=check_reaction)
            
            # Punto 2: Log cuando la reacción 👍 es válida
            print(f"Reacción 👍 del autor detectada y validada para el mensaje {final_message.id}")
            await registrar_log(f"Reacción 👍 del autor validada para el mensaje: {final_message.content}", final_message.author, final_message.channel, self.bot)
            
            # Punto 6: Marcar al usuario como que ya hizo su primera publicación
            if is_first_post_ever:
                self.redis_state.redis_client.set(f"user_first_post:{user_id_str}", "true")
                print(f"DEBUG: Usuario {final_message.author.name} marcado como 'first_post_completed'.")

        except asyncio.TimeoutError:
            # Punto 5: Si pasan los 120 segundos sin reaccionar 👍
            print(f"Timeout: No se detectó reacción 👍 para el mensaje {final_message.id}")
            await final_message.delete()
            await enviar_notificacion_temporal(final_message.channel, final_message.author,
                f"{final_message.author.mention} **Error:** No reaccionaste con 👍 a tu publicación en 120 segundos. Mensaje eliminado.")
            await registrar_falta(final_message.author, "Sin reacción 👍 en 120 segundos", final_message.channel)
            await registrar_log("Mensaje eliminado: Sin reacción 👍", final_message.author, final_message.channel, self.bot)
            
        await self.bot.process_commands(message) # Necesario para que otros comandos puedan procesarse

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

        # Punto 4: Registrar reacción 🔥 válida y loguear
        if str(reaction.emoji) == '🔥' and user != reaction.message.author:
            self.redis_state.save_reaction(user.id, reaction.message.id)
            print(f"Reacción 🔥 de {user.name} registrada para el mensaje {reaction.message.id}")
            target_message_url = reaction.message.jump_url if reaction.message.guild else "No URL (DM/Unknown)"
            await registrar_log(f"Usuario {user.name} reaccionó con 🔥 al mensaje de {reaction.message.author.name}: {target_message_url}", user, reaction.message.channel, self.bot)


async def setup(bot):
    await bot.add_cog(GoViralCog(bot))


async def enviar_notificacion_temporal(channel, user, content):
    msg = await channel.send(content)
    await asyncio.sleep(15)
    await msg.delete()
    try:
        # Asegurarse de que el bot puede enviar DMs
        if user.dm_channel is None:
            await user.create_dm() # Intenta crear el canal DM si no existe
        await user.send(f"⚠️ **Notificación de {channel.name}**: {content.replace(user.mention, '')}\n\n*Este es un mensaje automático del bot.*")
    except discord.Forbidden:
        print(f"Error: No se pudo enviar DM a {user.name}. Puede que tenga los DMs deshabilitados.")
    except Exception as e:
        print(f"Error inesperado al enviar DM a {user.name}: {e}")
