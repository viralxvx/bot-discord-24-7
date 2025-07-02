# cogs/inactivity_tracker.py

import discord
from discord.ext import commands, tasks
import time
from datetime import datetime, timedelta

import config
from utils.embed_generator import format_timestamp, get_current_timestamp

class InactivityTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.redis_state = bot.redis_state
        # Acceder al cog de FaltasManager después de que se cargue
        self.faltas_manager = None 
        
        self.inactivity_check_loop.start()
        self.proroga_reminder_loop.start()

    def cog_unload(self):
        self.inactivity_check_loop.cancel()
        self.proroga_reminder_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        # Retrasar la obtención para asegurar que FaltasManager ya está cargado
        await asyncio.sleep(1) 
        self.faltas_manager = self.bot.get_cog("FaltasManager")
        if not self.faltas_manager:
            print("ERROR: FaltasManager cog no encontrado. Las actualizaciones de tarjetas no funcionarán.")
            if config.CANAL_LOGS_ID:
                log_channel = self.bot.get_channel(config.CANAL_LOGS_ID)
                if log_channel:
                    await log_channel.send("⚠️ Error: FaltasManager cog no encontrado. Las actualizaciones de tarjetas de faltas no funcionarán correctamente.")

    @tasks.loop(hours=24) # Verifica cada 24 horas
    async def inactivity_check_loop(self):
        """
        Tarea programada para verificar la inactividad de los miembros y aplicar sanciones.
        """
        await self.bot.wait_until_ready()
        print("Iniciando verificación de inactividad...")
        guild = self.bot.get_guild(self.bot.guild_id) # Asegúrate de que tu bot.guild_id esté configurado
        if not guild:
            print("ERROR: Gremio no encontrado para la verificación de inactividad.")
            return

        current_time = get_current_timestamp()
        
        # Considerar solo miembros no bot
        for member in guild.members:
            if member.bot:
                continue

            user_id = member.id
            
            last_post_time = await self.redis_state.get_last_post_time(user_id)
            inactivity_status = await self.redis_state.get_inactivity_status(user_id)
            inactivity_ban_start = await self.redis_state.get_inactivity_ban_start(user_id)
            proroga_end_time = await self.redis_state.get_inactivity_extension_end(user_id)
            last_proroga_reason = await self.redis_state.get_last_proroga_reason(user_id)

            # --- Manejo de Prórrogas ---
            if proroga_end_time > 0:
                if current_time < proroga_end_time:
                    # Prórroga activa, saltar la verificación de inactividad para este usuario
                    # print(f"Usuario {member.display_name} tiene prórroga activa hasta {format_timestamp(proroga_end_time)}.")
                    await self.faltas_manager.update_user_fault_card(
                        user=member,
                        status="prorroga",
                        last_post_time=last_post_time,
                        inactivity_extension_end=proroga_end_time,
                        proroga_reason=last_proroga_reason
                    )
                    continue # Pasar al siguiente miembro
                else:
                    # Prórroga expirada
                    print(f"Prórroga de {member.display_name} ha expirado. Evaluando inactividad.")
                    await self.redis_state.delete_inactivity_extension_end(user_id)
                    # El usuario ahora es sujeto a la inactividad normal.
                    # Continuar con la lógica de inactividad para que se aplique si lleva 3 días inactivo.

            # --- Lógica de Baneo/Expulsión por Inactividad ---
            # Solo si no hay prórroga activa
            if current_time - last_post_time >= config.DIAS_INACTIVIDAD_PARA_BAN * 86400: # 86400 segundos en un día
                if inactivity_status == "none":
                    # Primer incidente de inactividad: Ban temporal
                    print(f"Usuario {member.display_name} inactivo por 3 días. Ban temporal.")
                    await self._handle_inactivity_action(member, "ban", last_post_time)
                elif inactivity_status == "first_ban":
                    # Segundo incidente de inactividad: Expulsión permanente
                    # Esta parte solo debería ejecutarse si el usuario ha sido desbaneado previamente
                    # y volvió a ser inactivo. El desbaneo se gestiona en la siguiente sección.
                    
                    # Verificamos si el ban ya terminó y el usuario volvió a ser inactivo.
                    # Si el usuario sigue baneado, no lo volvemos a evaluar hasta que el ban termine.
                    if inactivity_ban_start > 0 and current_time - inactivity_ban_start >= config.DURACION_BAN_DIAS * 86400:
                        # Ban terminó, y volvió a ser inactivo. Expulsar.
                        print(f"Usuario {member.display_name} reincidente tras baneo. Expulsión permanente.")
                        await self._handle_inactivity_action(member, "kick", last_post_time)
                    elif inactivity_ban_start == 0:
                        # Esto podría ocurrir si se saltó un estado. Mejor asumir kick.
                        print(f"Usuario {member.display_name} inactivo y ya tiene estado 'first_ban' sin ban activo. Expulsión permanente.")
                        await self._handle_inactivity_action(member, "kick", last_post_time)
                    else:
                        # El usuario está baneado actualmente y el ban no ha terminado.
                        # Actualizar su tarjeta para reflejar que sigue baneado.
                        await self.faltas_manager.update_user_fault_card(
                            user=member,
                            status="baneado",
                            last_post_time=last_post_time,
                            inactivity_ban_start=inactivity_ban_start
                        )

            # --- Desbaneo automático tras 7 días ---
            if inactivity_status == "first_ban" and inactivity_ban_start > 0:
                if current_time - inactivity_ban_start >= config.DURACION_BAN_DIAS * 86400:
                    # El baneo de 7 días ha terminado
                    try:
                        await guild.unban(discord.Object(id=user_id), reason="Fin de baneo por inactividad")
                        await self.redis_state.set_inactivity_status(user_id, "none") # Resetea el estado
                        await self.redis_state.delete_inactivity_ban_start(user_id)
                        
                        log_channel = self.bot.get_channel(config.CANAL_LOGS_ID)
                        if log_channel:
                            await log_channel.send(f"✅ Usuario {member.display_name} (ID: {user_id}) desbaneado automáticamente por fin de baneo de inactividad.")
                        await self._send_dm_notification(member, "desbaneo")

                        # Actualizar tarjeta de faltas
                        await self.faltas_manager.update_user_fault_card(
                            user=member,
                            status="activo",
                            last_post_time=last_post_time # Última publicación antes del ban
                        )

                        print(f"Usuario {member.display_name} (ID: {user_id}) desbaneado automáticamente.")
                    except discord.NotFound:
                        # Ya no está baneado, quizás fue desbaneado manualmente. Limpiar Redis.
                        await self.redis_state.set_inactivity_status(user_id, "none")
                        await self.redis_state.delete_inactivity_ban_start(user_id)
                        print(f"Usuario {member.display_name} (ID: {user_id}) no encontrado en lista de baneados, limpiando estado.")
                    except discord.Forbidden:
                        print(f"ERROR: No tengo permisos para desbanear al usuario {member.display_name}.")
                    except Exception as e:
                        print(f"ERROR inesperado al desbanear a {member.display_name}: {e}")
            elif inactivity_status == "none": # Si está activo y sin faltas
                 await self.faltas_manager.update_user_fault_card(
                    user=member,
                    status="activo",
                    last_post_time=last_post_time
                )


        print("Verificación de inactividad completada.")

    @tasks.loop(hours=12) # Revisa dos veces al día para recordatorios
    async def proroga_reminder_loop(self):
        """
        Tarea programada para recordar a los usuarios que su prórroga está a punto de expirar.
        """
        await self.bot.wait_until_ready()
        print("Iniciando verificación de recordatorios de prórroga...")
        guild = self.bot.get_guild(self.bot.guild_id)
        if not guild:
            return

        current_time = get_current_timestamp()
        
        # Recuperar todos los usuarios con prórrogas activas (puedes añadir un método a RedisState para esto)
        # Por ahora, simularemos iterando a través de todos los miembros y verificando.
        # Una implementación más eficiente sería tener una clave en Redis que liste los usuarios con prórroga.
        for member in guild.members:
            if member.bot:
                continue

            proroga_end_time = await self.redis_state.get_inactivity_extension_end(member.id)
            if proroga_end_time > 0:
                time_until_expiration = proroga_end_time - current_time
                
                if timedelta(hours=24 * config.DIAS_PRE_AVISO_PRORROGA) >= timedelta(seconds=time_until_expiration) > timedelta(hours=0):
                    # La prórroga expirará en config.DIAS_PRE_AVISO_PRORROGA días o menos, pero aún no ha expirado
                    
                    # Comprobar si ya se envió el recordatorio (para no spamear)
                    # Esto requeriría una clave adicional en Redis: proroga_reminder_sent:{user_id}:{timestamp_dia_envio}
                    # Por simplicidad, este ejemplo lo omite, pero es crucial en producción.
                    
                    await self._send_dm_notification(member, "proroga_reminder", proroga_end_time)
                    print(f"Recordatorio de prórroga enviado a {member.display_name}. Expira en {timedelta(seconds=time_until_expiration)}.")


    async def _handle_inactivity_action(self, member: discord.Member, action: str, last_post_time: float):
        """
        Realiza la acción de baneo o expulsión y actualiza el estado.
        """
        user_id = member.id
        guild = member.guild
        log_channel = self.bot.get_channel(config.CANAL_LOGS_ID)

        try:
            if action == "ban":
                await guild.ban(member, reason=f"Inactividad: {config.DIAS_INACTIVIDAD_PARA_BAN} días sin publicar (1er incidente)")
                await self.redis_state.set_inactivity_status(user_id, "first_ban")
                await self.redis_state.set_inactivity_ban_start(user_id, get_current_timestamp())
                
                if log_channel:
                    await log_channel.send(f"⛔️ Usuario {member.display_name} (ID: {user_id}) baneado automáticamente por inactividad. Duración: {config.DURACION_BAN_DIAS} días.")
                await self._send_dm_notification(member, "ban", config.DURACION_BAN_DIAS)
                
                await self.faltas_manager.update_user_fault_card(
                    user=member,
                    status="baneado",
                    last_post_time=last_post_time,
                    inactivity_ban_start=get_current_timestamp()
                )
                print(f"Usuario {member.display_name} baneado por inactividad.")

            elif action == "kick":
                await guild.kick(member, reason=f"Inactividad recurrente: {config.DIAS_INACTIVIDAD_PARA_BAN} días sin publicar tras baneo previo")
                await self.redis_state.set_inactivity_status(user_id, "kicked")
                await self.redis_state.delete_inactivity_ban_start(user_id) # Limpiar cualquier ban previo
                
                if log_channel:
                    await log_channel.send(f"❌ Usuario {member.display_name} (ID: {user_id}) expulsado automáticamente por inactividad recurrente.")
                await self._send_dm_notification(member, "kick")
                
                # Para expulsiones, la tarjeta del usuario debe ser eliminada
                if self.faltas_manager:
                    await self.faltas_manager.remove_user_fault_entry(user_id) # Need to add this method in FaltasManager
                print(f"Usuario {member.display_name} expulsado por inactividad recurrente.")

        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para {action} al usuario {member.display_name}.")
            if log_channel:
                await log_channel.send(f"🚨 ERROR de Permisos: No pude {action} al usuario {member.display_name} (ID: {user_id}).")
        except discord.HTTPException as e:
            print(f"ERROR HTTP al intentar {action} a {member.display_name}: {e}")
            if log_channel:
                await log_channel.send(f"🚨 ERROR HTTP al intentar {action} a {member.display_name} (ID: {user_id}): {e}")
        except Exception as e:
            print(f"ERROR inesperado en _handle_inactivity_action para {member.display_name}: {e}")
            if log_channel:
                await log_channel.send(f"🚨 ERROR inesperado al intentar {action} a {member.display_name} (ID: {user_id}): {e}")

    async def _send_dm_notification(self, user: discord.User, notification_type: str, *args):
        """
        Envía una notificación por DM al usuario.
        """
        try:
            if notification_type == "ban":
                duration_days = args[0]
                await user.send(
                    f"Hola {user.mention},\n\n"
                    f"Queremos informarte que has sido **baneado temporalmente por {duration_days} días** del servidor **GoViral** "
                    f"debido a inactividad prolongada ({config.DIAS_INACTIVIDAD_PARA_BAN} días sin publicar).\n\n"
                    f"Esta es la primera vez que se aplica esta medida. "
                    f"Serás desbaneado automáticamente al cabo de {duration_days} días. "
                    f"Si tras tu regreso vuelves a incurrir en inactividad, serás expulsado permanentemente.\n\n"
                    f"Por favor, revisa las normas en el canal de bienvenida."
                )
            elif notification_type == "kick":
                await user.send(
                    f"Hola {user.mention},\n\n"
                    f"Has sido **expulsado permanentemente** del servidor **GoViral** debido a inactividad recurrente. "
                    f"Anteriormente, fuiste baneado temporalmente por este motivo y, lamentablemente, "
                    f"la inactividad se repitió.\n\n"
                    f"Esta medida busca mantener activa y comprometida a la comunidad.\n"
                    f"Si consideras que ha sido un error, puedes intentar contactar a un administrador."
                )
            elif notification_type == "desbaneo":
                await user.send(
                    f"Hola {user.mention},\n\n"
                    f"¡Buenas noticias! Tu baneo temporal en el servidor **GoViral** ha finalizado. "
                    f"Puedes reingresar al servidor. Te recordamos la importancia de la participación activa. "
                    f"Si vuelves a pasar {config.DIAS_INACTIVIDAD_PARA_BAN} días sin publicar, serás expulsado permanentemente del servidor."
                )
            elif notification_type == "proroga_reminder":
                proroga_end_time = args[0]
                await user.send(
                    f"Hola {user.mention},\n\n"
                    f"Solo para recordarte que tu prórroga de inactividad en GoViral está por expirar el **{format_timestamp(proroga_end_time)}**.\n\n"
                    f"Por favor, asegúrate de realizar una publicación o de solicitar una nueva prórroga en el canal de soporte <#{config.CANAL_SOPORTE_ID}> antes de esa fecha "
                    f"para evitar sanciones automáticas por inactividad."
                )
        except discord.Forbidden:
            print(f"ERROR: No se pudo enviar DM a {user.display_name} (DMs bloqueados o privados).")
        except Exception as e:
            print(f"ERROR al enviar DM de notificación a {user.display_name}: {e}")


async def setup(bot):
    await bot.add_cog(InactivityTracker(bot))
