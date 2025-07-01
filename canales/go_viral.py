import discord
from discord.ext import commands
import re
import asyncio
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_LOGS  # Mantén CANAL_LOGS si lo necesitas para los logs

def setup(bot):
    @bot.event
    async def on_ready():
        print("Bot está listo, intentando enviar mensaje de bienvenida...")
        channel = bot.get_channel(1353824447131418676)  # ID directo del canal go-viral
        if channel:
            try:
                # Verificar si ya existe un mensaje de bienvenida fijado
                pinned_messages = await channel.pins()
                welcome_message_exists = any("Bienvenido a go-viral" in msg.content for msg in pinned_messages)
                
                if not welcome_message_exists:
                    welcome_message = await channel.send(
                        "📢 **Bienvenido a go-viral!** Por favor, sigue las reglas:\n"
                        "1. Publica solo URLs en el formato `https://x.com/usuario/status/123456...`.\n"
                        "2. Reacciona con 🔥 a las publicaciones de otros.\n"
                        "3. Reacciona con 👍 a tu propia publicación en 120 segundos.\n"
                        "¡Disfruta del canal!"
                    )
                    await welcome_message.pin()
                    await registrar_log("Mensaje de bienvenida enviado y fijado", bot.user, channel)
                    print("Mensaje de bienvenida enviado y fijado exitosamente")
                else:
                    print("El mensaje de bienvenida ya está fijado")
            except discord.errors.Forbidden:
                print("Error: El bot no tiene permisos para enviar mensajes o fijarlos en el canal")
            except discord.errors.HTTPException as e:
                print(f"Error HTTP al enviar o fijar el mensaje de bienvenida: {e}")
            except Exception as e:
                print(f"Error inesperado enviando mensaje de bienvenida: {e}")
        else:
            print("No se encontró el canal con ID: 1353824447131418676")

    @bot.event
    async def on_message(message):
        if message.channel.id != 1353824447131418676 or message.author.bot or message.pinned:
            await bot.process_commands(message)
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
                await registrar_log("Mensaje eliminado: URL inválida", message.author, message.channel)
                return

        # Verificar intervalo de publicaciones
        redis_state = RedisState()
        last_post = redis_state.get_last_post(message.author.id)
        recent_posts = redis_state.get_recent_posts(1353824447131418676)
        if last_post and len([p for p in recent_posts if p['author_id'] != message.author.id]) < 2:
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author, 
                f"{message.author.mention} **Error:** Debes esperar al menos 2 publicaciones válidas de otros usuarios antes de publicar nuevamente.")
            await registrar_falta(message.author, "Publicación antes de intervalo permitido", message.channel)
            await registrar_log("Mensaje eliminado: Intervalo no respetado", message.author, message.channel)
            return

        # Verificar reacciones 🔥 en publicaciones previas
        required_reactions = redis_state.get_required_reactions(message.author.id, 1353824447131418676)
        if not all(redis_state.has_reaction(message.author.id, post_id) for post_id in required_reactions):
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author, 
                f"{message.author.mention} **Error:** Debes reaccionar con 🔥 a todas las publicaciones posteriores a tu última publicación.")
            await registrar_falta(message.author, "Falta de reacciones 🔥", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacciones 🔥", message.author, message.channel)
            return

        # Corregir URL si es necesario
        if corrected_url:
            await message.delete()
            new_message = await message.channel.send(f"{corrected_url} (Corregido por el bot)")
            await registrar_log(f"URL corregida: {content} -> {corrected_url}", message.author, message.channel)
            await enviar_notificacion_temporal(message.channel, message.author, 
                f"{message.author.mention} **URL corregida:** Usa el formato `https://x.com/usuario/status/123456...` sin parámetros adicionales.")
            message = new_message

        # Guardar publicación en Redis
        redis_state.save_post(message.id, message.author.id, 1353824447131418676)

        # Esperar reacción 👍 del autor
        def check_reaction(reaction, user):
            return user == message.author and str(reaction.emoji) == '👍' and reaction.message.id == message.id

        try:
            await bot.wait_for('reaction_add', timeout=120, check=check_reaction)
        except asyncio.TimeoutError:
            await message.delete()
            await enviar_notificacion_temporal(message.channel, message.author, 
                f"{message.author.mention} **Error:** No reaccionaste con 👍 a tu publicación en 120 segundos.")
            await registrar_falta(message.author, "Sin reacción 👍 en 120 segundos", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacción 👍", message.author, message.channel)

        await bot.process_commands(message)

    @bot.event
    async def on_reaction_add(reaction, user):
        if reaction.message.channel.id != 1353824447131418676 or user.bot:
            return

        # Prohibir 🔥 en propia publicación
        if str(reaction.emoji) == '🔥' and user == reaction.message.author:
            await reaction.remove(user)
            await enviar_notificacion_temporal(reaction.message.channel, user, 
                f"{user.mention} **Error:** No puedes reaccionar con 🔥 a tu propia publicación.")
            await registrar_falta(user, "Reacción 🔥 en propia publicación", reaction.message.channel)
            await registrar_log("Reacción eliminada: 🔥 en propia publicación", user, reaction.message.channel)

        # Registrar reacción 🔥 válida
        if str(reaction.emoji) == '🔥' and user != reaction.message.author:
            RedisState().save_reaction(user.id, reaction.message.id)

    async def enviar_notificacion_temporal(channel, user, content):
        msg = await channel.send(content)
        await asyncio.sleep(15)
        await msg.delete()
        try:
            await user.send(f"⚠️ Falta: {content.replace(user.mention, '')}")
        except:
            pass
