import discord
from discord.ext import commands
import re
import asyncio
import datetime
import os
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta
from config import CANAL_OBJETIVO, CANAL_LOGS

def setup(bot):
    @bot.event
    async def on_ready():
        print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
        print("------")
        
        # Encontrar el canal objetivo por nombre
        channel = None
        for guild in bot.guilds:
            for ch in guild.text_channels:
                if ch.id == CANAL_OBJETIVO:
                    channel = ch
                    break
            if channel:
                break
        
        if not channel:
            print(f"Error: No se encontró el canal con ID {CANAL_OBJETIVO}")
            return

        # Limpiar mensajes anteriores del bot
        try:
            deleted = await channel.purge(limit=50, check=lambda m: m.author == bot.user)
            print(f"Se borraron {len(deleted)} mensajes antiguos del bot")
        except Exception as e:
            print(f"Error al limpiar mensajes: {e}")

        # Mensaje de bienvenida (formato simple que funcionaba antes)
        welcome_message = (
            "🧵 **REGLAS DEL CANAL GO-VIRAL** 🧵\n\n"
            "🎉 **¡BIENVENIDOS A GO-VIRAL!** 🎉\n"
            "¡Nos alegra tenerte aquí! Este es tu espacio para hacer crecer tu contenido de **𝕏 (Twitter)**.\n\n"
            "📋 **REGLAS PRINCIPALES:**\n"
            "1. 🔗 **Formato correcto:** https://x.com/usuario/status/1234567890\n"
            "2. 👍 **Reacciona con 👍 a tu propia publicación en 120 segundos**\n"
            "3. 🔥 **Reacciona con 🔥 a TODAS las publicaciones posteriores a la tuya antes de publicar de nuevo**\n"
            "4. ⏳ **Espera mínimo 2 publicaciones válidas de otros usuarios**\n\n"
            "⚠️ **Infracciones generan faltas:** Formato incorrecto, sin reacción 👍, falta de 🔥, publicar fuera de turno\n"
            "🤖 **El bot corregirá URLs, eliminará publicaciones inválidas y notificará faltas**\n\n"
            "¡Juntos hacemos crecer nuestra comunidad! 🚀"
        )

        try:
            msg = await channel.send(welcome_message)
            await msg.pin()
            print("Mensaje de bienvenida enviado y anclado exitosamente!")
            await registrar_log("Mensaje de bienvenida enviado", bot.user, channel)
        except Exception as e:
            print(f"Error al enviar mensaje de bienvenida: {e}")

    @bot.event
    async def on_message(message):
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
            await bot.process_commands(message)
            return

        content = message.content.strip()
        redis_state = RedisState()

        # 1. Validar formato de URL
        url_pattern = r'^https://x\.com/\w+/status/\d+$'
        if not re.match(url_pattern, content):
            # Intentar corregir URL
            match = re.search(r'(https://x\.com/\w+/status/\d+)', content)
            if match:
                corrected_url = match.group(1)
                await message.delete()
                new_msg = await message.channel.send(f"{corrected_url} (Corregido por el bot)")
                await registrar_log(f"URL corregida: {content} -> {corrected_url}", message.author, message.channel)
                await enviar_notificacion(
                    message.channel, 
                    message.author, 
                    f"**URL corregida:** Usa el formato correcto `https://x.com/usuario/status/123456...`"
                )
                message = new_msg
            else:
                await message.delete()
                await enviar_notificacion(
                    message.channel, 
                    message.author, 
                    f"**Error:** URL inválida. Formato requerido: `https://x.com/usuario/status/123456...`"
                )
                await registrar_falta(message.author, "URL inválida", message.channel)
                return

        # 2. Verificar intervalo de publicaciones
        last_post = redis_state.get_last_post(message.author.id)
        if last_post:
            recent_posts = redis_state.get_recent_posts(CANAL_OBJETIVO)
            others_posts = [p for p in recent_posts if p['author_id'] != message.author.id]
            
            if len(others_posts) < 2:
                await message.delete()
                await enviar_notificacion(
                    message.channel, 
                    message.author, 
                    f"**Error:** Espera al menos 2 publicaciones de otros usuarios antes de publicar de nuevo"
                )
                await registrar_falta(message.author, "Publicación antes de intervalo", message.channel)
                return

        # 3. Verificar reacciones 🔥 en publicaciones previas
        required_reactions = redis_state.get_required_reactions(message.author.id, CANAL_OBJETIVO)
        if not all(redis_state.has_reaction(message.author.id, post_id) for post_id in required_reactions):
            await message.delete()
            await enviar_notificacion(
                message.channel, 
                message.author, 
                f"**Error:** Debes reaccionar con 🔥 a TODAS las publicaciones posteriores a tu última"
            )
            await registrar_falta(message.author, "Falta de reacciones 🔥", message.channel)
            return

        # Guardar publicación
        redis_state.save_post(message.id, message.author.id, CANAL_OBJETIVO)

        # 4. Esperar reacción 👍 del autor
        def check_reaction(reaction, user):
            return (
                user == message.author and 
                str(reaction.emoji) == '👍' and 
                reaction.message.id == message.id
            )

        try:
            await bot.wait_for('reaction_add', timeout=120, check=check_reaction)
        except asyncio.TimeoutError:
            await message.delete()
            await enviar_notificacion(
                message.channel, 
                message.author, 
                f"**Error:** No reaccionaste con 👍 a tu publicación en 120 segundos"
            )
            await registrar_falta(message.author, "Sin reacción 👍", message.channel)

    @bot.event
    async def on_reaction_add(reaction, user):
        if reaction.message.channel.id != CANAL_OBJETIVO or user.bot:
            return

        # 1. Prevenir 🔥 en propia publicación
        if str(reaction.emoji) == '🔥' and user == reaction.message.author:
            await reaction.remove(user)
            await enviar_notificacion(
                reaction.message.channel, 
                user, 
                f"**Error:** No puedes reaccionar con 🔥 a tu propia publicación"
            )
            await registrar_falta(user, "🔥 en propia publicación", reaction.message.channel)

        # 2. Registrar reacción 🔥 válida
        if str(reaction.emoji) == '🔥' and user != reaction.message.author:
            RedisState().save_reaction(user.id, reaction.message.id)

    async def enviar_notificacion(channel, user, content):
        """Envía notificación temporal en el canal y DM al usuario"""
        try:
            # Notificación en el canal (se autodestruye)
            msg = await channel.send(f"{user.mention} {content}")
            await asyncio.sleep(15)
            await msg.delete()
        except:
            pass
        
        try:
            # Notificación por DM
            await user.send(f"⚠️ **Notificación:** {content}")
        except:
            pass
