import discord
from discord.ext import commands
import re
import asyncio
import json # Necesario para parsear los posts de Redis
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_OBJETIVO

# Importar los textos de mensajes y notificaciones desde los nuevos archivos
from mensajes.go_viral import WELCOME_MESSAGE_TITLE, WELCOME_MESSAGE_IMAGE_URL, WELCOME_MESSAGE_TEXT, FIRST_POST_WELCOME_MESSAGE_TEXT
from notificaciones.go_viral import (
    URL_INVALIDA, INTERVALO_NO_RESPETADO, REACCIONES_PENDIENTES_CHANNEL, 
    REACCIONES_PENDIENTES_DM, LINK_CORREGIDO_CHANNEL, NO_REACCION_THUMBS_UP, 
    REACCION_FIRE_PROPIA_PUBLICACION, REACCION_NO_PERMITIDA
)

class GoViralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis_state = RedisState()

    async def go_viral_on_ready(self):
        print(f"Lógica on_ready de GoViralCog iniciada para el canal {CANAL_OBJETIVO}...")

        channel_go_viral = self.bot.get_channel(CANAL_OBJETIVO)
        if not channel_go_viral:
            print(f"ERROR: No se pudo encontrar el canal go-viral con la ID: {CANAL_OBJETIVO}")
            return

        # --- Borrar mensaje de bienvenida antiguo si existe (Punto 2 de la solicitud anterior) ---
        existing_welcome_message_id = self.redis_state.redis_client.get(f"welcome_message_active:{CANAL_OBJETIVO}")
        if existing_welcome_message_id:
            try:
                old_message = await channel_go_viral.fetch_message(int(existing_welcome_message_id))
                await old_message.delete()
                print(f"DEBUG: Mensaje de bienvenida antiguo (ID: {existing_welcome_message_id}) borrado.")
                await registrar_log("Mensaje de bienvenida antiguo borrado para actualizar", self.bot.user, channel_go_viral, self.bot)
            except discord.NotFound:
                print(f"DEBUG: Mensaje de bienvenida antiguo (ID: {existing_welcome_message_id}) no encontrado. Posiblemente ya borrado.")
                self.redis_state.redis_client.delete(f"welcome_message_active:{CANAL_OBJETIVO}") # Limpiar Redis si no existe
            except discord.Forbidden:
                print(f"ERROR: No tengo permisos para borrar el mensaje de bienvenida antiguo en el canal '{channel_go_viral.name}'.")
            except Exception as e:
                print(f"ERROR al intentar borrar mensaje de bienvenida antiguo: {e}")
        else:
            print("DEBUG: No se encontró mensaje de bienvenida antiguo en Redis.")

        # --- Siempre enviar el nuevo mensaje de bienvenida después de la limpieza ---
        print(f"DEBUG: Enviando nuevo mensaje de bienvenida para el canal {CANAL_OBJETIVO}.")
        embed = discord.Embed(title=WELCOME_MESSAGE_TITLE, description=WELCOME_MESSAGE_TEXT, color=discord.Color.gold())
        embed.set_image(url=WELCOME_MESSAGE_IMAGE_URL)
        try:
            sent_message = await channel_go_viral.send(embed=embed)
            self.redis_state.set_welcome_message_id(sent_message.id, CANAL_OBJETIVO)
            print("Mensaje de bienvenida al canal go-viral enviado exitosamente desde GoViralCog.")
            await registrar_log("Mensaje de bienvenida enviado al canal go-viral", self.bot.user, channel_go_viral, self.bot)
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para enviar el embed en el canal '{channel_go_viral.name}'.")
        except Exception as e:
            print(f"ERROR al enviar el mensaje de bienvenida al canal '{channel_go_viral.name}': {e}")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
            await self.bot.process_commands(message)
            return

        redis_state = self.redis_state
        user_id_str = str(message.author.id)
        original_author = message.author 
        
        # Verificar si es la primera publicación del usuario
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
                await enviar_notificacion_temporal(message.channel, original_author, URL_INVALIDA)
                await registrar_falta(original_author, "URL inválida", message.channel)
                await registrar_log("Mensaje eliminado: URL inválida", original_author, message.channel, self.bot)
                return
        
        # ------------------------------------------------------------------------------------------------
        # Validación de intervalo de publicaciones (esperar 2 válidas de otros)
        last_post_time = redis_state.get_last_post_time(original_author.id)
        recent_posts_count_others = len([p for p in redis_state.get_recent_posts(CANAL_OBJETIVO) if str(p['author_id']) != user_id_str])

        if not is_first_post_ever:
            if last_post_time and recent_posts_count_others < 2:
                await message.delete()
                await enviar_notificacion_temporal(message.channel, original_author, INTERVALO_NO_RESPETADO)
                await registrar_falta(original_author, "Publicación antes de intervalo permitido", message.channel)
                await registrar_log("Mensaje eliminado: Intervalo no respetado", original_author, message.channel, self.bot)
                return

        # ------------------------------------------------------------------------------------------------
        # Validación de reacciones 🔥 en publicaciones previas
        if not is_first_post_ever:
            required_reactions_details = redis_state.get_required_reactions_details(original_author.id, CANAL_OBJETIVO)
            missing_reactions = []
            
            for post_data in required_reactions_details:
                if not redis_state.has_reaction(original_author.id, post_data['message_id']):
                    missing_reactions.append(post_data)

            if missing_reactions:
                await message.delete()
                
                missing_info_list = []
                for mr in missing_reactions:
                    missing_info_list.append(f"- **{mr['author_name']}**: <{mr['url']}>")

                missing_info_str = "\n".join(missing_info_list)

                channel_msg = REACCIONES_PENDIENTES_CHANNEL.format(missing_info_str=missing_info_str)
                dm_msg = REACCIONES_PENDIENTES_DM.format(channel_name=message.channel.name, missing_info_str=missing_info_str)

                await enviar_notificacion_temporal(message.channel, original_author, channel_msg, dm_msg) # Pasa el dm_msg explícitamente
                await registrar_falta(original_author, "Falta de reacciones 🔥 pendientes", message.channel)
                await registrar_log(f"Mensaje eliminado: Sin reacciones 🔥 pendientes. Faltantes: {missing_info_str}", original_author, message.channel, self.bot)
                return
        
        # ------------------------------------------------------------------------------------------------
        # Corrección de URL automática (usando Webhook para mantener el autor original)
        final_message_content = corrected_url if corrected_url else content
        final_message = None

        try:
            webhook = await self.redis_state.get_or_create_webhook(message.channel)
            await message.delete()
            
            webhook_message = await webhook.send(
                content=final_message_content,
                username=original_author.display_name,
                avatar_url=original_author.display_avatar.url,
                wait=True
            )
            
            if corrected_url:
                await enviar_notificacion_temporal(message.channel, original_author,
                    f"{original_author.mention} {LINK_CORREGIDO_CHANNEL}")
                await registrar_log(f"URL corregida (via webhook): {content} -> {corrected_url}", original_author, message.channel, self.bot)
            
            final_message = webhook_message 
            
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para gestionar webhooks o enviar via webhook en el canal '{message.channel.name}'.")
            final_message = await message.channel.send(f"{final_message_content} (Publicado por el bot debido a error de permisos/webhook)")
            if corrected_url:
                await enviar_notificacion_temporal(message.channel, original_author,
                    f"{original_author.mention} {LINK_CORREGIDO_CHANNEL} Fue republicado por el bot.")
                await registrar_log(f"URL corregida (fallback bot): {content} -> {corrected_url}", original_author, message.channel, self.bot)

        except Exception as e:
            print(f"ERROR al enviar mensaje via webhook o gestionar: {e}")
            final_message = await message.channel.send(f"{final_message_content} (Publicado por el bot debido a un error)")
            if corrected_url:
                await enviar_notificacion_temporal(message.channel, original_author,
                    f"{original_author.mention} {LINK_CORREGIDO_CHANNEL} Fue republicado por el bot debido a un error.")
                await registrar_log(f"URL corregida (fallback bot): {content} -> {corrected_url}", original_author, message.channel, self.bot)

        # ------------------------------------------------------------------------------------------------
        # Guardar publicación en Redis
        self.redis_state.save_post(final_message.id, original_author.id, CANAL_OBJETIVO, final_message.content, original_author.name)
        await registrar_log("Nueva publicación válida registrada (pendiente de 👍)", original_author, final_message.channel, self.bot)

        # ------------------------------------------------------------------------------------------------
        # Mensaje de bienvenida para usuario nuevo (Punto 3)
        if is_first_post_ever:
            # Marcamos al usuario como 'no nuevo' para futuras interacciones
            self.redis_state.redis_client.set(f"user_first_post:{user_id_str}", "true") 
            
            personalized_welcome_content = FIRST_POST_WELCOME_MESSAGE_TEXT.format(user_mention=original_author.mention)
            try:
                first_post_welcome_message = await message.channel.send(personalized_welcome_content)
                print(f"DEBUG: Mensaje de bienvenida personalizado enviado a {original_author.name} (ID: {first_post_welcome_message.id})")
                await registrar_log(f"Mensaje de bienvenida personalizado enviado a usuario nuevo: {original_author.name}", self.bot.user, message.channel, self.bot)

                # Programar su eliminación después de 1 hora
                self.bot.loop.create_task(self.delete_message_after_delay(first_post_welcome_message, 3600)) # 3600 segundos = 1 hora
            except discord.Forbidden:
                print(f"ERROR: No tengo permisos para enviar el mensaje de bienvenida personalizado en el canal '{message.channel.name}'.")
            except Exception as e:
                print(f"ERROR al enviar mensaje de bienvenida personalizado: {e}")

        # ------------------------------------------------------------------------------------------------
        # Esperar reacción 👍 del autor
        def check_reaction(reaction, user_check):
            print(f"DEBUG REACTION CHECK: Reaction emoji: {str(reaction.emoji)}, User ID: {user_check.id} ({user_check.name}), Message ID: {reaction.message.id}")
            print(f"DEBUG REACTION CHECK: Expected original author ID: {original_author.id}, Expected final message ID: {final_message.id}")
            
            return user_check.id == original_author.id and str(reaction.emoji) == '👍' and reaction.message.id == final_message.id

        try:
            print(f"DEBUG: Esperando reacción 👍 para mensaje {final_message.id} por {original_author.name}...")
            await self.bot.wait_for('reaction_add', timeout=120, check=check_reaction)
            
            print(f"Reacción 👍 del autor detectada y validada para el mensaje {final_message.id}")
            await registrar_log(f"Reacción 👍 del autor validada para el mensaje: {final_message.content}", original_author, final_message.channel, self.bot)
            
        except asyncio.TimeoutError:
            print(f"Timeout: No se detectó reacción 👍 para el mensaje {final_message.id}")
            await final_message.delete()
            await enviar_notificacion_temporal(final_message.channel, original_author, 
                f"{original_author.mention} {NO_REACCION_THUMBS_UP}")
            await registrar_falta(original_author, "Sin reacción 👍 en 120 segundos", final_message.channel)
            await registrar_log("Mensaje eliminado: Sin reacción 👍", original_author, final_message.channel, self.bot)
            
        await self.bot.process_commands(message)

    # Método para borrar mensajes después de un retraso (para el mensaje de bienvenida a nuevos usuarios)
    async def delete_message_after_delay(self, message: discord.Message, delay_seconds: int):
        await asyncio.sleep(delay_seconds)
        try:
            await message.delete()
            print(f"DEBUG: Mensaje temporal (ID: {message.id}) borrado después de {delay_seconds} segundos.")
        except discord.NotFound:
            print(f"DEBUG: Mensaje temporal (ID: {message.id}) ya borrado o no encontrado.")
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para borrar el mensaje temporal (ID: {message.id}).")
        except Exception as e:
            print(f"ERROR inesperado al borrar mensaje temporal (ID: {message.id}): {e}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.channel.id != CANAL_OBJETIVO or user.bot:
            return

        # ------------------------------------------------------------------------------------------------
        # Punto 4: Canal-go viral solo debe permitir 🔥 y 👍. Cualquier otra reacción debe ser eliminada.
        if str(reaction.emoji) not in ['👍', '🔥']:
            try:
                await reaction.remove(user)
                print(f"DEBUG: Reacción no permitida '{str(reaction.emoji)}' de {user.name} eliminada.")
            except discord.Forbidden:
                print(f"ERROR: No tengo permisos para eliminar la reacción no permitida de {user.name} (permisos).")
            
            channel_msg = f"{user.mention} {REACCION_NO_PERMITIDA}"
            await enviar_notificacion_temporal(reaction.message.channel, user, channel_msg)
            await registrar_log(f"Reacción no permitida eliminada: '{str(reaction.emoji)}' por {user.name} en mensaje {reaction.message.id}", user, reaction.message.channel, self.bot)
            return # Salir después de manejar la reacción no permitida

        # ------------------------------------------------------------------------------------------------
        # Obtener el ID del autor original del mensaje desde Redis para validaciones de reacciones
        original_author_id_of_message = None
        recent_posts_raw = self.redis_state.redis_client.lrange(f"recent_posts:{CANAL_OBJETIVO}", 0, -1)
        author_name_for_log = "Desconocido" # Default para el log

        for p_json in recent_posts_raw:
            post_data = json.loads(p_json)
            if str(post_data['message_id']) == str(reaction.message.id):
                original_author_id_of_message = int(post_data['author_id'])
                author_name_for_log = post_data['author_name']
                break

        if original_author_id_of_message is None:
            print(f"WARNING: No se encontró información del post {reaction.message.id} en Redis para la reacción de {user.name}.")
            # Si no se encuentra la info en Redis, no podemos validar si es su propia publicación para 🔥.
            # Podríamos decidir borrar la reacción 🔥 para ser cautelosos, pero para 👍, se asume que la lógica en on_message ya maneja.
            # Por ahora, si no hay info, permitimos la reacción 🔥, pero no se registrará como "válida" en Redis.
            pass # Continuar con las siguientes validaciones si es 👍, o pasar si es 🔥 y no hay info.

        # ------------------------------------------------------------------------------------------------
        # Prohibir 🔥 en propia publicación (Punto 4)
        if str(reaction.emoji) == '🔥':
            if original_author_id_of_message is not None and user.id == original_author_id_of_message:
                try:
                    await reaction.remove(user)
                    print(f"Reacción 🔥 de {user.name} en su propia publicación (ID: {reaction.message.id}) eliminada.")
                except discord.Forbidden:
                    print(f"Error: No se pudo eliminar la reacción 🔥 de {user.name} (permisos).")
                await enviar_notificacion_temporal(reaction.message.channel, user,
                    f"{user.mention} {REACCION_FIRE_PROPIA_PUBLICACION}")
                await registrar_falta(user, "Reacción 🔥 en propia publicación", reaction.message.channel)
                await registrar_log("Reacción eliminada: 🔥 en propia publicación", user, reaction.message.channel, self.bot)
                return # Salir después de manejar la reacción prohibida

            # Registrar reacción 🔥 válida de otro usuario
            elif original_author_id_of_message is not None and user.id != original_author_id_of_message:
                self.redis_state.save_reaction(user.id, reaction.message.id)
                print(f"Reacción 🔥 de {user.name} registrada para el mensaje {reaction.message.id}")
                target_message_url = reaction.message.jump_url if reaction.message.guild else "No URL (DM/Unknown)"
                await registrar_log(f"Usuario {user.name} reaccionó con 🔥 al mensaje de {author_name_for_log} (ID: {reaction.message.id}): {target_message_url}", user, reaction.message.channel, self.bot)


async def setup(bot):
    await bot.add_cog(GoViralCog(bot))

# La función enviar_notificacion_temporal se mantiene, pero la adaptamos para recibir dm_content
# y se asegura de registrar en logs y enviar al DM.
async def enviar_notificacion_temporal(channel, user, channel_content, dm_content=None):
    msg = await channel.send(channel_content)
    await asyncio.sleep(15)
    try:
        await msg.delete()
    except discord.NotFound:
        print(f"DEBUG: Mensaje temporal (ID: {msg.id}) ya borrado o no encontrado.")
    except discord.Forbidden:
        print(f"ERROR: No tengo permisos para borrar el mensaje temporal (ID: {msg.id}).")
    except Exception as e:
        print(f"ERROR inesperado al borrar mensaje temporal (ID: {msg.id}): {e}")

    # Enviar al DM del usuario como constancia y registrar en logs
    if dm_content is None: # Si no se provee un contenido específico para DM, usa el del canal
        dm_content = f"⚠️ **Notificación de {channel.name}**: {channel_content.replace(user.mention, '')}\n\n*Este es un mensaje automático del bot.*"

    try:
        if user.dm_channel is None:
            await user.create_dm()
        await user.send(dm_content)
        print(f"DEBUG: Notificación enviada por DM a {user.name}.")
    except discord.Forbidden:
        print(f"Error: No se pudo enviar DM a {user.name}. Puede que tenga los DMs deshabilitados.")
    except Exception as e:
        print(f"Error inesperado al enviar DM a {user.name}: {e}")

    # Ya que `registrar_log` se llamará desde la función principal que llama a esta, no lo duplicamos aquí.
    # Por ejemplo, en on_message, después de llamar a enviar_notificacion_temporal, se llama a registrar_log.
    # Para el caso de "Reacción no permitida", lo registramos directamente aquí para simplificar.
    # Pero para otros casos (URL inválida, etc.), registrar_log ya está en el flujo principal.
