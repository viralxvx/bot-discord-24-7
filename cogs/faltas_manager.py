# cogs/faltas_manager.py

import discord
from discord.ext import commands, tasks
import asyncio
import time
import re
from datetime import datetime, timedelta

import config
from utils.embed_generator import create_fault_card_embed, format_timestamp, get_current_timestamp

class FaltasManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Asegúrate de que RedisState esté disponible a través del bot
        self.redis_state = bot.redis_state
        self.faults_history_cache = {} # Caché para el historial de faltas de usuarios (ej. para faltas menores)
                                        # Formato: {user_id: [{"timestamp": float, "reason": str}]}
        
        # Iniciar la tarea de limpieza y sincronización al bot estar listo
        self.bot.loop.create_task(self.setup_faltas_channel())

    async def _get_faltas_channel(self):
        """Helper para obtener el canal de faltas."""
        channel = self.bot.get_channel(config.CANAL_FALTAS_ID)
        if not channel:
            print(f"ERROR: Canal de faltas (ID: {config.CANAL_FALTAS_ID}) no encontrado.")
            if config.CANAL_LOGS_ID:
                log_channel = self.bot.get_channel(config.CANAL_LOGS_ID)
                if log_channel:
                    await log_channel.send(f"⚠️ Error: El canal de faltas (ID: `{config.CANAL_FALTAS_ID}`) no fue encontrado. Algunas funciones podrían no operar correctamente.")
            return None
        return channel

    async def setup_faltas_channel(self):
        """
        Rutina ejecutada al inicio del bot para limpiar y sincronizar el canal #faltas.
        """
        await self.bot.wait_until_ready()
        faltas_channel = await self._get_faltas_channel()
        if not faltas_channel:
            return

        print("Iniciando rutina de limpieza y sincronización del canal #faltas...")

        # 1. Gestionar el mensaje del panel principal
        panel_message_id = await self.redis_state.get_faltas_panel_message_id()
        panel_message = None
        
        if panel_message_id:
            try:
                panel_message = await faltas_channel.fetch_message(panel_message_id)
                # Actualizar el contenido si es necesario (ej. si config.FALTAS_PANEL_CONTENT cambia)
                if panel_message.content != config.FALTAS_PANEL_CONTENT:
                    await panel_message.edit(content=config.FALTAS_PANEL_CONTENT)
                print(f"Mensaje del panel de faltas recuperado y actualizado: {panel_message.id}")
            except discord.NotFound:
                print("Mensaje del panel de faltas no encontrado en Discord, creándolo de nuevo.")
                panel_message_id = None # Marcar para crear uno nuevo
            except discord.Forbidden:
                print("ERROR: No tengo permisos para leer/editar el mensaje del panel de faltas.")
                panel_message_id = None
            except Exception as e:
                print(f"ERROR inesperado al gestionar mensaje del panel de faltas: {e}")
                panel_message_id = None

        if not panel_message_id:
            try:
                panel_message = await faltas_channel.send(config.FALTAS_PANEL_CONTENT)
                await self.redis_state.set_faltas_panel_message_id(panel_message.id)
                print(f"Mensaje del panel de faltas creado y guardado: {panel_message.id}")
            except discord.Forbidden:
                print("ERROR: No tengo permisos para enviar mensajes en el canal de faltas.")
                return

        # 2. Sincronizar tarjetas de usuario y limpiar mensajes no gestionados
        redis_user_card_ids = await self.redis_state.get_all_fault_card_message_ids()
        
        messages_to_delete = []
        synced_user_ids = set()

        async for message in faltas_channel.history(limit=None): # Recorre todo el historial para una limpieza exhaustiva
            if message.id == panel_message_id:
                continue # Ignorar el mensaje del panel

            if message.author == self.bot.user and message.embeds:
                # Es un mensaje de nuestro bot con un embed
                embed = message.embeds[0]
                user_id = self._extract_user_id_from_embed(embed)

                if user_id:
                    user_id_str = str(user_id)
                    synced_user_ids.add(user_id_str)
                    
                    # Si la tarjeta ya está en Redis y el ID coincide, todo bien.
                    # Si no, significa que Redis no la conoce (quizás fue purgado o desincronizado).
                    # Guardamos el ID en Redis para sincronizar.
                    if user_id_str not in redis_user_card_ids or redis_user_card_ids[user_id_str] != str(message.id):
                        await self.redis_state.set_user_fault_card_message_id(user_id, message.id)
                        print(f"Sincronizado: Tarjeta de {user_id} encontrada en canal, Redis actualizado.")
                else:
                    # Embed del bot sin un user_id válido, posiblemente un mensaje antiguo o corrupto
                    messages_to_delete.append(message)
            else:
                # No es un mensaje del bot o no tiene embed, debe ser eliminado
                messages_to_delete.append(message)

        # Eliminar mensajes no deseados
        if messages_to_delete:
            print(f"Eliminando {len(messages_to_delete)} mensajes no gestionados en #faltas...")
            try:
                # Discord.py purge es más eficiente para muchos mensajes
                await faltas_channel.delete_messages(messages_to_delete)
            except discord.Forbidden:
                print("ERROR: No tengo permisos para purgar mensajes en #faltas.")
            except Exception as e:
                print(f"ERROR al purgar mensajes en #faltas: {e}")

        # 3. Limpiar entradas de Redis para tarjetas que ya no están en Discord (fueron borradas manualmente, etc.)
        all_redis_keys = await self.redis_state.get_all_fault_card_message_ids()
        for user_id_str, message_id_str in all_redis_keys.items():
            if user_id_str not in synced_user_ids:
                # La tarjeta de este usuario NO fue encontrada en el canal durante la sincronización
                await self.redis_state.delete_user_fault_card_message_id(int(user_id_str))
                print(f"Limpiado: Entrada de Redis para {user_id_str} eliminada (tarjeta no encontrada en Discord).")

        print("Sincronización del canal #faltas completada.")


    # --- Listener para proteger la integridad del canal #faltas ---
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignorar mensajes del propio bot para evitar bucles
        if message.author.bot:
            return

        # Si el mensaje es en el canal de faltas
        if message.channel.id == config.CANAL_FALTAS_ID:
            try:
                # Eliminar el mensaje
                await message.delete()

                # Opcional: Enviar un DM al usuario explicando
                try:
                    await message.author.send(
                        f"Hola {message.author.mention},\n\n"
                        f"Tu mensaje en el canal {message.channel.mention} ha sido eliminado "
                        f"automáticamente. Este canal está **reservado exclusivamente** para el "
                        f"sistema de seguimiento de actividad y faltas del bot. "
                        f"No está permitido enviar mensajes, enlaces ni contenido en este canal. "
                        f"Por favor, consulta las normas del servidor para más información sobre el uso de los canales."
                    )
                except discord.Forbidden:
                    # El bot no pudo enviar el DM (ej. usuario tiene los DMs cerrados)
                    print(f"ADVERTENCIA: No se pudo enviar DM a {message.author.name} ({message.author.id}) después de eliminar mensaje en #faltas.")

            except discord.Forbidden:
                print(f"ERROR: No tengo permisos para borrar mensajes en el canal {message.channel.name} ({message.channel.id}). "
                      f"Asegúrate de que el bot tenga el permiso 'Gestionar Mensajes'.")
            except discord.HTTPException as e:
                print(f"ERROR HTTP al borrar mensaje en {message.channel.name}: {e}")

    # --- Listener para eliminar tarjetas de usuarios expulsados/que abandonan ---
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return # No gestionar bots

        print(f"Miembro {member.display_name} ({member.id}) ha abandonado el servidor. Eliminando su tarjeta de faltas si existe.")
        faltas_channel = await self._get_faltas_channel()
        if not faltas_channel:
            return

        message_id = await self.redis_state.get_user_fault_card_message_id(member.id)
        if message_id:
            try:
                message_to_delete = await faltas_channel.fetch_message(message_id)
                await message_to_delete.delete()
                await self.redis_state.delete_user_fault_card_message_id(member.id)
                print(f"Tarjeta de faltas para {member.display_name} eliminada de #faltas.")
            except discord.NotFound:
                await self.redis_state.delete_user_fault_card_message_id(member.id)
                print(f"Tarjeta de faltas para {member.display_name} no encontrada en Discord, eliminada solo de Redis.")
            except discord.Forbidden:
                print(f"ERROR: No tengo permisos para borrar la tarjeta de faltas de {member.display_name}.")
            except Exception as e:
                print(f"ERROR al eliminar tarjeta de faltas de {member.display_name}: {e}")

    # --- Función para actualizar la tarjeta de faltas de un usuario ---
    async def update_user_fault_card(
        self,
        user: discord.Member,
        status: str, # "activo", "baneado", "expulsado", "prorroga", "falta_menor"
        last_post_time: float,
        inactivity_ban_start: float = 0.0,
        inactivity_extension_end: float = 0.0,
        proroga_reason: str = "No especificada",
        new_fault_details: dict = None # {"timestamp": float, "reason": str}
    ):
        faltas_channel = await self._get_faltas_channel()
        if not faltas_channel:
            return

        # Recuperar o inicializar historial de faltas menores para la tarjeta
        # Este historial es solo para mostrar faltas no de inactividad, que ya tienen su status.
        user_faults_key = f"faults_history:{user.id}"
        # Fetch existing history from Redis or cache if needed
        # For simplicity, this example will just add the new_fault_details if provided.
        # A more robust system might store a JSON list of past minor faults in Redis.
        
        # Para este ejemplo, si hay una nueva falta, la añadimos al historial de la tarjeta.
        # Considera que para un sistema más completo, podrías guardar un JSON en Redis para
        # el historial de faltas menores.
        history_list = self.faults_history_cache.get(user.id, [])
        if new_fault_details and new_fault_details not in history_list:
            history_list.append(new_fault_details)
            self.faults_history_cache[user.id] = history_list # Actualizar caché

        # Limitar el historial a mostrar en el embed (ej. las últimas 3)
        display_history = sorted(history_list, key=lambda x: x['timestamp'], reverse=True)[:3]

        embed = create_fault_card_embed(
            user=user,
            status=status,
            last_post_time=last_post_time,
            inactivity_ban_start=inactivity_ban_start,
            inactivity_extension_end=inactivity_extension_end,
            proroga_reason=proroga_reason,
            faults_history=display_history
        )

        message_id = await self.redis_state.get_user_fault_card_message_id(user.id)
        
        try:
            if message_id:
                # Intentar editar la tarjeta existente
                message = await faltas_channel.fetch_message(message_id)
                await message.edit(embed=embed)
                print(f"Tarjeta de faltas de {user.display_name} ({user.id}) actualizada.")
            else:
                # Crear una nueva tarjeta si no existe
                message = await faltas_channel.send(embed=embed)
                await self.redis_state.set_user_fault_card_message_id(user.id, message.id)
                print(f"Nueva tarjeta de faltas para {user.display_name} ({user.id}) creada.")
        except discord.NotFound:
            # El mensaje no existe en Discord aunque Redis lo tuviera. Crear uno nuevo.
            print(f"Tarjeta de faltas para {user.display_name} no encontrada en Discord, creando una nueva.")
            await self.redis_state.delete_user_fault_card_message_id(user.id) # Limpiar el ID viejo
            message = await faltas_channel.send(embed=embed)
            await self.redis_state.set_user_fault_card_message_id(user.id, message.id)
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para enviar/editar mensajes en el canal de faltas para {user.display_name}.")
        except Exception as e:
            print(f"ERROR inesperado al gestionar la tarjeta de faltas de {user.display_name}: {e}")

    def _extract_user_id_from_embed(self, embed: discord.Embed) -> int:
        """
        Extrae el ID de usuario del embed de la tarjeta de faltas.
        Asume que el ID está en el footer o en el título.
        """
        if embed.footer and embed.footer.text and "ID de Usuario:" in embed.footer.text:
            match = re.search(r'ID de Usuario:\s*(\d+)', embed.footer.text)
            if match:
                return int(match.group(1))
        if embed.title:
            match = re.search(r'ID:\s*(\d+)', embed.title) # Si lo pones en el título
            if match:
                return int(match.group(1))
        return None

async def setup(bot):
    await bot.add_cog(FaltasManager(bot))
