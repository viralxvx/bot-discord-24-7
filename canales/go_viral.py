import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta, timezone
import os
from config import (
    CANAL_GO_VIRAL_ID, CANAL_LOGS_ID, MIN_REACCIONES_GO_VIRAL, TIEMPO_ESPERA_POST_MINUTOS,
    WELCOME_MESSAGE_TITLE, WELCOME_MESSAGE_IMAGE_URL, WELCOME_MESSAGE_TEXT # ¡NUEVO!
)
from canales.logs import registrar_log
from canales.faltas import registrar_falta 

class GoViralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.go_viral_channel = None
        self.log_channel = None
        self.welcome_message_task = None
        self.webhook_cache = {} 

    async def go_viral_on_ready(self):
        print(f"Lógica on_ready de GoViralCog iniciada para el canal {CANAL_GO_VIRAL_ID}...")
        try:
            self.go_viral_channel = await self.bot.fetch_channel(CANAL_GO_VIRAL_ID)
            print(f"Canal Go Viral obtenido: {self.go_viral_channel.name}")
        except discord.NotFound:
            print(f"ERROR: Canal Go Viral con ID {CANAL_GO_VIRAL_ID} no encontrado.")
            await registrar_log(f"ERROR: Canal Go Viral no encontrado (ID: {CANAL_GO_VIRAL_ID})", self.bot.user, None, self.bot)
            self.go_viral_channel = None
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para acceder al canal Go Viral con ID {CANAL_GO_VIRAL_ID}.")
            await registrar_log(f"ERROR: Permisos denegados para canal Go Viral (ID: {CANAL_GO_VIRAL_ID})", self.bot.user, None, self.bot)
            self.go_viral_channel = None
        except Exception as e:
            print(f"ERROR inesperado al obtener el canal Go Viral: {e}")
            await registrar_log(f"ERROR: Fallo al obtener canal Go Viral: {e}", self.bot.user, None, self.bot)
            self.go_viral_channel = None

        try:
            self.log_channel = await self.bot.fetch_channel(CANAL_LOGS_ID)
            print(f"Canal de Logs obtenido: {self.log_channel.name}")
        except discord.NotFound:
            print(f"ERROR: Canal de Logs con ID {CANAL_LOGS_ID} no encontrado.")
            self.log_channel = None
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para acceder al canal de Logs con ID {CANAL_LOGS_ID}.")
            self.log_channel = None
        except Exception as e:
            print(f"ERROR inesperado al obtener el canal de Logs: {e}")
            self.log_channel = None

        if self.go_viral_channel:
            self.welcome_message_task = self.bot.loop.create_task(self.send_welcome_message())
        else:
            print("No se iniciará la tarea de mensaje de bienvenida porque el canal Go Viral no está disponible.")

    async def get_webhook(self, channel):
        if channel.id not in self.webhook_cache:
            if hasattr(self.bot, 'redis_state') and self.bot.redis_state:
                webhook = await self.bot.redis_state.get_or_create_webhook(channel)
                self.webhook_cache[channel.id] = webhook
            else:
                print("Advertencia: RedisState no está disponible. No se puede obtener/crear webhook persistente.")
                try:
                    new_webhook = await channel.create_webhook(name=f"{channel.name}-go-viral-bot-temp")
                    self.webhook_cache[channel.id] = new_webhook
                    print(f"Webhook temporal creado para el canal {channel.name}")
                except Exception as e:
                    print(f"ERROR: No se pudo crear webhook temporal para {channel.name}: {e}")
                    return None
        return self.webhook_cache[channel.id]

    async def send_welcome_message(self):
        if not self.go_viral_channel:
            print("No se puede enviar el mensaje de bienvenida: canal Go Viral no disponible.")
            return

        welcome_message_id = await self.bot.redis_state.get_welcome_message_id(self.go_viral_channel.id)
        existing_message = None

        if welcome_message_id:
            try:
                existing_message = await self.go_viral_channel.fetch_message(welcome_message_id)
                print("Mensaje de bienvenida existente encontrado.")
            except discord.NotFound:
                print("Mensaje de bienvenida existente no encontrado (borrado o ID incorrecto).")
                existing_message = None
            except discord.Forbidden:
                print("No tengo permisos para buscar el mensaje de bienvenida existente.")
                existing_message = None
            except Exception as e:
                print(f"Error al buscar mensaje de bienvenida existente: {e}")
                existing_message = None

        # --- AQUI ES DONDE SE USA EL NUEVO CONTENIDO DE config.py ---
        embed = discord.Embed(
            title=WELCOME_MESSAGE_TITLE,
            description=WELCOME_MESSAGE_TEXT,
            color=discord.Color.gold()
        )
        if WELCOME_MESSAGE_IMAGE_URL:
            embed.set_image(url=WELCOME_MESSAGE_IMAGE_URL)
        embed.set_footer(text="Bot actualizado • Sistema automatizado • Apoyo 24/7") # Pie de página fijo

        if existing_message:
            try:
                await existing_message.edit(embed=embed)
                print("Mensaje de bienvenida existente actualizado.")
            except Exception as e:
                print(f"Error al editar mensaje de bienvenida existente: {e}")
                existing_message = None
        
        if not existing_message:
            try:
                new_message = await self.go_viral_channel.send(embed=embed)
                await self.bot.redis_state.set_welcome_message_id(new_message.id, self.go_viral_channel.id)
                print("Nuevo mensaje de bienvenida enviado y ID guardado.")
            except Exception as e:
                print(f"Error al enviar nuevo mensaje de bienvenida: {e}")
                await registrar_log(f"ERROR: Fallo al enviar mensaje de bienvenida: {e}", self.bot.user, None, self.bot)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Esta lógica de bienvenida a nuevos miembros es diferente al mensaje fijo del canal
        if hasattr(self.bot, 'redis_state') and self.bot.redis_state:
            if await self.bot.redis_state.is_user_welcomed(member.id):
                print(f"Usuario {member.display_name} (ID: {member.id}) ya había sido bienvenido. Saltando mensaje.")
                await registrar_log(f"Usuario {member.display_name} (ID: {member.id}) intentó unirse de nuevo, ya bienvenido.", member, None, self.bot)
                return 
            else:
                print(f"Usuario {member.display_name} (ID: {member.id}) es nuevo o no marcado. Enviando mensaje de bienvenida.")
        else:
            print("Advertencia: RedisState no está disponible. No se puede verificar si el usuario ya fue bienvenido.")
            await registrar_log("Advertencia: RedisState no disponible para verificar usuario bienvenido.", self.bot.user, None, self.bot)

        if self.go_viral_channel:
            welcome_embed_member = discord.Embed( # Embed diferente para miembros nuevos
                title=f"¡Bienvenido, {member.display_name}! 👋",
                description=f"¡Nos alegra tenerte en nuestro servidor! Asegúrate de revisar las reglas en {self.go_viral_channel.mention} y diviértete.",
                color=discord.Color.green()
            )
            welcome_embed_member.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            welcome_embed_member.set_footer(text="¡Disfruta tu estancia!")

            try:
                await self.go_viral_channel.send(embed=welcome_embed_member)
                print(f"Mensaje de bienvenida enviado a {member.display_name} en {self.go_viral_channel.name}.")
                await registrar_log(f"Mensaje de bienvenida enviado a {member.display_name}.", member, self.go_viral_channel, self.bot)
                
                if hasattr(self.bot, 'redis_state') and self.bot.redis_state:
                    await self.bot.redis_state.set_user_welcomed(member.id)

            except discord.Forbidden:
                print(f"ERROR: No tengo permisos para enviar mensajes en {self.go_viral_channel.name}.")
                await registrar_log(f"ERROR: Permisos denegados para enviar mensaje de bienvenida en {self.go_viral_channel.name}.", self.bot.user, self.go_viral_channel, self.bot)
            except Exception as e:
                print(f"ERROR inesperado al enviar mensaje de bienvenida: {e}")
                await registrar_log(f"ERROR: Fallo al enviar mensaje de bienvenida a {member.display_name}: {e}", self.bot.user, self.go_viral_channel, self.bot)
        else:
            print(f"No se pudo enviar mensaje de bienvenida a {member.display_name}: canal Go Viral no disponible.")
            await registrar_log(f"No se pudo enviar mensaje de bienvenida a {member.display_name}: canal Go Viral no disponible.", self.bot.user, None, self.bot)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id == CANAL_GO_VIRAL_ID:
            if hasattr(self.bot, 'redis_state') and self.bot.redis_state:
                await self.bot.redis_state.save_post(message.id, message.author.id, message.channel.id, message.content, message.author.display_name)
                print(f"Post de {message.author.display_name} guardado en Redis.")
            else:
                print("Advertencia: RedisState no está disponible. No se guardará el post.")
                await registrar_log("Advertencia: RedisState no disponible para guardar posts.", self.bot.user, message.channel, self.bot)

            if hasattr(self.bot, 'redis_state') and self.bot.redis_state:
                last_post_time = await self.bot.redis_state.get_last_post_time(message.author.id)
                current_time = datetime.now(timezone.utc).timestamp()
                
                if last_post_time:
                    time_since_last_post = (current_time - last_post_time) / 60 
                    if time_since_last_post < TIEMPO_ESPERA_POST_MINUTOS:
                        remaining_time = TIEMPO_ESPERA_POST_MINUTOS - time_since_last_post
                        await message.delete()
                        await message.author.send(
                            f"¡Hola! Solo puedes publicar un post en el canal Go Viral cada {TIEMPO_ESPERA_POST_MINUTOS} minutos. "
                            f"Por favor, espera {remaining_time:.1f} minutos más antes de publicar de nuevo."
                        )
                        await registrar_falta(message.author, f"Intentó postear antes de tiempo ({TIEMPO_ESPERA_POST_MINUTOS} min)", message.channel, self.bot)
                        return
            
                await self.bot.redis_state.set_last_post_time(message.author.id, current_time)
                print(f"Tiempo de último post de {message.author.display_name} actualizado.")
            else:
                print("Advertencia: RedisState no está disponible. No se aplicará el límite de tiempo de posts.")
                await registrar_log("Advertencia: RedisState no disponible para límite de tiempo de posts.", self.bot.user, message.channel, self.bot)

            if hasattr(self.bot, 'redis_state') and self.bot.redis_state:
                required_reactions = await self.bot.redis_state.get_required_reactions_details(message.author.id, message.channel.id)
                if required_reactions:
                    dm_message = (
                        f"¡Hola {message.author.display_name}! Para que tus posts en el canal Go Viral cuenten, "
                        f"necesitas reaccionar a los posts de otros usuarios. "
                        f"Aquí hay algunos posts recientes que requieren tu reacción:\n\n"
                    )
                    for post in required_reactions:
                        dm_message += f"- Post de **{post['author_name']}**: [Ir al post]({post['url']})\n"
                    
                    dm_message += "\n¡Reacciona para ayudar a la comunidad y a ti mismo!"
                    
                    try:
                        await message.author.send(dm_message)
                        print(f"DM enviado a {message.author.display_name} sobre reacciones requeridas.")
                        await registrar_log(f"DM enviado a {message.author.display_name} sobre reacciones requeridas.", message.author, message.channel, self.bot)
                    except discord.Forbidden:
                        print(f"No se pudo enviar DM a {message.author.display_name} (DMs deshabilitados).")
                        await registrar_log(f"ERROR: No se pudo enviar DM a {message.author.display_name} (DMs deshabilitados).", message.author, message.channel, self.bot)
            else:
                print("Advertencia: RedisState no está disponible. No se verificarán reacciones requeridas.")
                await registrar_log("Advertencia: RedisState no disponible para verificar reacciones requeridas.", self.bot.user, message.channel, self.bot)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return

        if payload.channel_id == CANAL_GO_VIRAL_ID:
            channel = self.bot.get_channel(payload.channel_id)
            if not channel:
                channel = await self.bot.fetch_channel(payload.channel_id)

            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                print(f"Mensaje {payload.message_id} no encontrado para la reacción.")
                return
            except discord.Forbidden:
                print(f"No tengo permisos para buscar el mensaje {payload.message_id}.")
                return
            except Exception as e:
                print(f"Error al buscar mensaje para la reacción: {e}")
                return

            if message.author.id == payload.member.id:
                print(f"Reacción de {payload.member.display_name} en su propio post. Ignorando.")
                await registrar_falta(payload.member, "Reaccionó a su propio post en Go Viral", channel, self.bot)
                try:
                    await message.remove_reaction(payload.emoji, payload.member)
                except Exception as e:
                    print(f"Error al remover reacción propia: {e}")
                return

            if hasattr(self.bot, 'redis_state') and self.bot.redis_state:
                if await self.bot.redis_state.has_reaction(payload.member.id, payload.message_id):
                    print(f"Usuario {payload.member.display_name} ya reaccionó a este post. Ignorando.")
                    await registrar_falta(payload.member, "Reaccionó múltiples veces al mismo post en Go Viral", channel, self.bot)
                    try:
                        await message.remove_reaction(payload.emoji, payload.member)
                    except Exception as e:
                        print(f"Error al remover reacción duplicada: {e}")
                    return
                
                posts_by_same_author = await self.bot.redis_state.get_posts_by_author(message.author.id, channel.id)
                reacted_to_same_author = False
                for post in posts_by_same_author:
                    if await self.bot.redis_state.has_reaction(payload.member.id, post['message_id']):
                        reacted_to_same_author = True
                        break
                
                if reacted_to_same_author:
                    print(f"Usuario {payload.member.display_name} ya reaccionó a un post de {message.author.display_name}. Ignorando.")
                    await registrar_falta(payload.member, "Reaccionó a múltiples posts del mismo autor en Go Viral", channel, self.bot)
                    try:
                        await message.remove_reaction(payload.emoji, payload.member)
                    except Exception as e:
                        print(f"Error al remover reacción por autor duplicado: {e}")
                    return

                await self.bot.redis_state.save_reaction(payload.member.id, payload.message_id)
                print(f"Reacción de {payload.member.display_name} en post {message.id} guardada en Redis.")
            else:
                print("Advertencia: RedisState no está disponible. No se guardará la reacción ni se validarán reglas.")
                await registrar_log("Advertencia: RedisState no disponible para reacciones.", self.bot.user, channel, self.bot)
                return 

            unique_reactions = set()
            for reaction in message.reactions:
                async for user in reaction.users():
                    if not user.bot: 
                        unique_reactions.add(user.id)
            
            print(f"Post {message.id} ahora tiene {len(unique_reactions)} reacciones únicas.")

            if len(unique_reactions) >= MIN_REACCIONES_GO_VIRAL:
                print(f"Post {message.id} alcanzó {MIN_REACCIONES_GO_VIRAL} reacciones únicas. Promocionando...")
                
                webhook = await self.get_webhook(channel)
                if webhook:
                    promoted_embed = discord.Embed(
                        title="¡POST VIRAL! 🎉",
                        description=f"¡El post de {message.author.mention} ha alcanzado {MIN_REACCIONES_GO_VIRAL} reacciones únicas y se ha vuelto viral!",
                        color=discord.Color.blue()
                    )
                    promoted_embed.add_field(name="Contenido Original", value=message.content[:1024], inline=False)
                    promoted_embed.add_field(name="Ir al Post", value=f"[Haz clic aquí]({message.jump_url})", inline=False)
                    promoted_embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                    promoted_embed.set_footer(text="¡Felicidades!")

                    try:
                        await webhook.send(embed=promoted_embed, username=message.author.display_name, avatar_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                        print(f"Post de {message.author.display_name} promocionado via webhook.")
                        await registrar_log(f"Post de {message.author.display_name} promocionado.", message.author, channel, self.bot)
                        
                    except Exception as e:
                        print(f"ERROR: Fallo al promocionar post via webhook: {e}")
                        await registrar_log(f"ERROR: Fallo al promocionar post via webhook: {e}", self.bot.user, channel, self.bot)
                else:
                    print("ERROR: No se pudo obtener el webhook para promocionar el post.")
                    await registrar_log("ERROR: No se pudo obtener webhook para promocionar post.", self.bot.user, channel, self.bot)

async def setup(bot):
    await bot.add_cog(GoViralCog(bot))
