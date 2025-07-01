import discord
from discord.ext import commands
import re
import asyncio
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_OBJETIVO # CANAL_LOGS no es necesario aquí, ya que registrar_log lo tiene

def setup(bot):
    # --- ¡IMPORTANTE! ELIMINAR O COMENTAR LA SIGUIENTE SECCIÓN DE on_ready ---
    # @bot.event
    # async def on_ready():
    #     # Toda esta lógica se ha movido al on_ready de main.py
    #     pass # O puedes borrar todo este bloque si lo prefieres

    @bot.event
    async def on_message(message):
        # Asegúrate de que bot.process_commands(message) solo se llame una vez y donde debe
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
            await bot.process_commands(message) # Si no es el canal objetivo o es un bot, procesa comandos y sale
            return

        # Validar formato de la URL
        url_pattern = r'^https://x\.com/\w+/status/\d+$'
        content = message.content.strip()
        corrected_url = None
        # Intentar corregir URL si tiene parámetros adicionales
        if not re.match(url_pattern, content):
            try:
                base_url = re.match(r'(https://x\.com/\w+/status/\d+)', content).group(1)
                corrected_url = base_url
            except AttributeError:
                await message.delete()
                await enviar_notificacion_temporal(message.channel, message.author,
                    f"{message.author.mention} **Error:** La URL no es válida. Usa el formato: `https://x.com/usuario/status/123456...`")
                await registrar_falta(message.author, "URL inválida", message.channel)
                await registrar_log("Mensaje eliminado: URL inválida", message.author, message.channel, bot) # Pasar el bot
                return

        # Verificar intervalo de publicaciones
        redis_state = RedisState()
        last_post = redis_state.get_last_post(message.author.id)
        recent_posts = redis_state.get_recent_posts(CANAL_OBJETIVO)
        # La lógica para 'len([p for p in recent_posts if p['author_id'] != message.author.id]) < 2' puede necesitar
        # una revisión si RedisState.get_recent_posts no devuelve los IDs decodificados como int
        # Asegúrate de que los IDs del author_id se comparen como int(message.author.id)
        if last_post and len([p for p in recent_posts if p['author_id'] != message.author.id]) < 2:
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **Error:** Debes esperar al menos 2 publicaciones válidas de otros usuarios antes de publicar nuevamente.")
            await registrar_falta(message.author, "Publicación antes de intervalo permitido", message.channel)
            await registrar_log("Mensaje eliminado: Intervalo no respetado", message.author, message.channel, bot) # Pasar el bot
            return

        # Verificar reacciones 🔥 en publicaciones previas
        # Aquí también, asegúrate de que has_reaction y get_required_reactions manejen los IDs correctamente (int vs bytes)
        required_reactions = redis_state.get_required_reactions(message.author.id, CANAL_OBJETIVO)
        if not all(redis_state.has_reaction(message.author.id, post_id) for post_id in required_reactions):
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **Error:** Debes reaccionar con 🔥 a todas las publicaciones posteriores a tu última publicación.")
            await registrar_falta(message.author, "Falta de reacciones 🔥", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacciones 🔥", message.author, message.channel, bot) # Pasar el bot
            return

        # Corregir URL si es necesario
        if corrected_url:
            await message.delete()
            new_message = await message.channel.send(f"{corrected_url} (Corregido por el bot)")
            await registrar_log(f"URL corregida: {content} -> {corrected_url}", message.author, message.channel, bot) # Pasar el bot
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **URL corregida:** Usa el formato `https://x.com/usuario/status/123456...` sin parámetros adicionales.")
            message = new_message # Actualiza la referencia del mensaje al nuevo mensaje corregido

        # Guardar publicación en Redis
        redis_state.save_post(message.id, message.author.id, CANAL_OBJETIVO)
        await registrar_log("Nueva publicación válida registrada", message.author, message.channel, bot) # Nuevo log

        # Esperar reacción 👍 del autor
        def check_reaction(reaction, user):
            return user == message.author and str(reaction.emoji) == '👍' and reaction.message.id == message.id

        try:
            await bot.wait_for('reaction_add', timeout=120, check=check_reaction)
            print(f"Reacción 👍 del autor detectada para el mensaje {message.id}")
        except asyncio.TimeoutError:
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author,
                f"{message.author.mention} **Error:** No reaccionaste con 👍 a tu publicación en 120 segundos.")
            await registrar_falta(message.author, "Sin reacción 👍 en 120 segundos", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacción 👍", message.author, message.channel, bot) # Pasar el bot
            return

        # Al final de on_message, después de toda tu lógica
        await bot.process_commands(message)


    @bot.event
    async def on_reaction_add(reaction, user):
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
            await registrar_log("Reacción eliminada: 🔥 en propia publicación", user, reaction.message.channel, bot) # Pasar el bot
            return

        # Registrar reacción 🔥 válida
        if str(reaction.emoji) == '🔥' and user != reaction.message.author:
            RedisState().save_reaction(user.id, reaction.message.id)
            print(f"Reacción 🔥 de {user.name} registrada para el mensaje {reaction.message.id}")


    async def enviar_notificacion_temporal(channel, user, content):
        msg = await channel.send(content)
        await asyncio.sleep(15)
        await msg.delete()
        # Asegúrate de que el bot pueda enviar DMs. Los intents deberían cubrirlo.
        try:
            await user.send(f"⚠️ **Notificación de {channel.name}**: {content.replace(user.mention, '')}\n\n*Este es un mensaje automático del bot.*")
        except discord.Forbidden:
            print(f"Error: No se pudo enviar DM a {user.name}. Puede que tenga los DMs deshabilitados.")
