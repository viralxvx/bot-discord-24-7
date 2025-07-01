import discord
from discord.ext import commands
import re
import asyncio
import traceback
import logging
from datetime import datetime
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_OBJETIVO, CANAL_LOGS

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('go_viral_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variable global para rastrear el mensaje de reglas actual
mensaje_reglas_actual = None

async def debug_bot_permissions(bot, canal):
    """Función de debugging para verificar permisos del bot"""
    try:
        logger.info("=== VERIFICANDO PERMISOS DEL BOT ===")
        
        if not canal:
            logger.error(f"❌ CANAL ES None - ID buscado: {CANAL_OBJETIVO}")
            return False
            
        logger.info(f"✅ Canal encontrado: {canal.name} (ID: {canal.id})")
        
        # Verificar si el bot está en el servidor
        if not canal.guild.me:
            logger.error("❌ Bot no encontrado en el servidor")
            return False
            
        logger.info(f"✅ Bot encontrado en servidor: {canal.guild.me.display_name}")
        
        # Verificar permisos específicos
        permisos = canal.permissions_for(canal.guild.me)
        permisos_necesarios = {
            'send_messages': permisos.send_messages,
            'manage_messages': permisos.manage_messages,
            'pin_messages': permisos.pin_messages,
            'read_message_history': permisos.read_message_history,
            'view_channel': permisos.view_channel
        }
        
        logger.info("=== PERMISOS DEL BOT ===")
        for permiso, tiene in permisos_necesarios.items():
            status = "✅" if tiene else "❌"
            logger.info(f"{status} {permiso}: {tiene}")
            
        faltan_permisos = [p for p, t in permisos_necesarios.items() if not t]
        if faltan_permisos:
            logger.error(f"❌ FALTAN PERMISOS: {', '.join(faltan_permisos)}")
            return False
            
        logger.info("✅ Todos los permisos necesarios están disponibles")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando permisos: {type(e).__name__} - {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def debug_redis_connection():
    """Función de debugging para verificar conexión a Redis"""
    try:
        logger.info("=== VERIFICANDO CONEXIÓN REDIS ===")
        redis_state = RedisState()
        
        # Test básico de conexión
        test_key = "test_connection"
        test_value = "test_value"
        redis_state.client.set(test_key, test_value, ex=10)
        retrieved = redis_state.client.get(test_key)
        
        if retrieved and retrieved.decode() == test_value:
            logger.info("✅ Conexión Redis funcional")
            redis_state.client.delete(test_key)
            return True
        else:
            logger.error("❌ Redis no responde correctamente")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error conexión Redis: {type(e).__name__} - {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def enviar_reglas_canal(bot):
    """Envía y fija las reglas optimizadas en el canal objetivo CON DEBUGGING COMPLETO"""
    global mensaje_reglas_actual
    
    logger.info("=== INICIANDO PROCESO DE ENVÍO DE REGLAS ===")
    
    try:
        # Paso 1: Obtener canal
        logger.info(f"Paso 1: Buscando canal ID {CANAL_OBJETIVO}")
        canal = bot.get_channel(CANAL_OBJETIVO)
        
        if not canal:
            logger.error(f"❌ FALLA EN PASO 1: Canal {CANAL_OBJETIVO} no encontrado")
            
            # Intentar buscar en todos los canales del bot
            logger.info("Buscando en todos los canales disponibles...")
            for guild in bot.guilds:
                logger.info(f"Servidor: {guild.name} (ID: {guild.id})")
                for channel in guild.text_channels:
                    logger.info(f"  - Canal: {channel.name} (ID: {channel.id})")
            return False

        logger.info(f"✅ PASO 1 EXITOSO: Canal encontrado: {canal.name}")

        # Paso 2: Verificar permisos
        logger.info("Paso 2: Verificando permisos")
        if not await debug_bot_permissions(bot, canal):
            logger.error("❌ FALLA EN PASO 2: Permisos insuficientes")
            return False
        logger.info("✅ PASO 2 EXITOSO: Permisos verificados")

        # Paso 3: Verificar Redis
        logger.info("Paso 3: Verificando conexión Redis")
        if not await debug_redis_connection():
            logger.error("❌ FALLA EN PASO 3: Redis no disponible")
            # Continuar sin Redis si es necesario
        else:
            logger.info("✅ PASO 3 EXITOSO: Redis conectado")

        # Paso 4: Preparar mensaje
        logger.info("Paso 4: Preparando mensaje de reglas")
        mensaje_reglas = """# 🧵 **REGLAS GO-VIRAL** 🧵

🎉 **¡BIENVENIDOS!** Espacio para hacer crecer tu contenido de **𝕏** con apoyo mutuo.

## 📋 **REGLAS PRINCIPALES**

### 🔗 **FORMATO CORRECTO**
✅ `https://x.com/usuario/status/1931928250735026238`
❌ `https://x.com/usuario/status/1931928250735026238?s=46&t=...`

### 👍 **VALIDACIÓN**
• Reacciona con **👍** a tu post (120 segundos máximo)
• Sin reacción = eliminación automática

### 🔥 **APOYO MUTUO**
• Reacciona con **🔥** a posts posteriores al tuyo
• **REQUISITO:** Apoya en **𝕏** primero (RT + LIKE + COMENTARIO)
• Espera 2 publicaciones válidas antes de tu próximo post

## ⚠️ **FALTAS AUTOMÁTICAS**
• Formato incorrecto • No reaccionar a tiempo • Publicar sin apoyar
• Usar 🔥 en tu propio post • No respetar intervalos

## 🤖 **BOT AUTOMÁTICO**
✅ Corrige URLs automáticamente
📬 Notificaciones temporales (15s)
📝 Registro en logs y DM
🗑️ Elimina publicaciones inválidas

## 🏆 **CONSEJOS**
1. Lee las reglas antes de participar
2. Apoya genuinamente en 𝕏 antes de reaccionar
3. Mantén formato exacto de URLs
4. Sé constante con reacciones
5. Respeta turnos de otros usuarios

**¡Juntos hacemos crecer nuestra comunidad! 🚀**

*Bot 24/7 • Sistema automatizado • Apoyo mutuo*

🟢 **BOT ONLINE** - {timestamp}"""
        
        # Agregar timestamp
        import time
        mensaje_final = mensaje_reglas.replace("{timestamp}", f"<t:{int(time.time())}:R>")
        
        logger.info(f"Longitud del mensaje: {len(mensaje_final)}/2000 caracteres")
        
        if len(mensaje_final) > 2000:
            logger.error(f"❌ FALLA EN PASO 4: Mensaje excede límite ({len(mensaje_final)}/2000)")
            return False
        logger.info("✅ PASO 4 EXITOSO: Mensaje preparado")

        # Paso 5: Limpiar mensajes anteriores
        logger.info("Paso 5: Limpiando mensajes anteriores")
        deleted = 0
        try:
            async for message in canal.history(limit=50):
                if message.author == bot.user and "REGLAS GO-VIRAL" in message.content:
                    try:
                        logger.info(f"Despineando mensaje ID: {message.id}")
                        await message.unpin()
                        await asyncio.sleep(0.5)
                    except discord.NotFound:
                        logger.info("Mensaje ya no existe para despin")
                    except Exception as e:
                        logger.warning(f"Error al despinear: {e}")
                    
                    try:
                        logger.info(f"Eliminando mensaje ID: {message.id}")
                        await message.delete()
                        deleted += 1
                    except discord.NotFound:
                        logger.info("Mensaje ya eliminado")
                    except Exception as e:
                        logger.warning(f"Error al eliminar: {e}")
                    
                    await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
        
        logger.info(f"✅ PASO 5 EXITOSO: {deleted} mensajes eliminados")

        # Paso 6: Enviar nuevo mensaje
        logger.info("Paso 6: Enviando nuevo mensaje")
        await asyncio.sleep(2)  # Pausa antes de enviar
        
        try:
            mensaje_enviado = await canal.send(mensaje_final)
            mensaje_reglas_actual = mensaje_enviado
            logger.info(f"✅ MENSAJE ENVIADO EXITOSAMENTE: ID {mensaje_enviado.id}")
        except Exception as e:
            logger.error(f"❌ FALLA EN PASO 6: Error enviando mensaje: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

        # Paso 7: Fijar mensaje
        logger.info("Paso 7: Intentando fijar mensaje")
        try:
            await mensaje_enviado.pin(reason="Reglas actualizadas Go-Viral")
            logger.info("✅ MENSAJE FIJADO EXITOSAMENTE")
        except discord.HTTPException as e:
            logger.error(f"❌ Error HTTP al fijar: {e}")
            if e.code == 30003:  # Límite de pins
                logger.info("Límite de pins alcanzado, intentando limpiar...")
                try:
                    pins = await canal.pins()
                    logger.info(f"Pins actuales: {len(pins)}")
                    for i, pin in enumerate(pins[-3:]):
                        if pin.author != bot.user:
                            logger.info(f"Despineando pin antiguo {i+1}: {pin.id}")
                            await pin.unpin()
                            await asyncio.sleep(1)
                    
                    # Reintentar fijar
                    await mensaje_enviado.pin(reason="Reglas actualizadas Go-Viral (reintento)")
                    logger.info("✅ MENSAJE FIJADO DESPUÉS DE LIMPIAR PINS")
                except Exception as e2:
                    logger.error(f"❌ Error en reintento de pin: {e2}")
            else:
                logger.error(f"Error de pin no manejado: {e}")
        except Exception as e:
            logger.error(f"❌ Error inesperado al fijar: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        # Paso 8: Guardar en Redis y logs
        logger.info("Paso 8: Guardando referencias")
        try:
            # Guardar en Redis
            redis_state = RedisState()
            redis_state.set_welcome_message_id(mensaje_enviado.id, CANAL_OBJETIVO)
            logger.info("✅ ID guardado en Redis")
        except Exception as e:
            logger.warning(f"Error guardando en Redis: {e}")

        try:
            # Registrar en logs
            await registrar_log(
                f"✅ Reglas go-viral publicadas y fijadas ({len(mensaje_final)} caracteres)", 
                bot.user, 
                canal
            )
            logger.info("✅ Log registrado")
        except Exception as e:
            logger.warning(f"Error registrando log: {e}")

        logger.info("=== PROCESO COMPLETADO EXITOSAMENTE ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO EN ENVÍO DE REGLAS: {type(e).__name__} - {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return False

async def cleanup_on_disconnect(bot):
    """Limpia mensajes de reglas cuando el bot se desconecta"""
    global mensaje_reglas_actual
    
    logger.info("=== INICIANDO CLEANUP AL DESCONECTAR ===")
    
    try:
        if mensaje_reglas_actual:
            canal = bot.get_channel(CANAL_OBJETIVO)
            if canal:
                try:
                    content = mensaje_reglas_actual.content
                    if "🟢 **BOT ONLINE**" in content:
                        content = content.replace("🟢 **BOT ONLINE**", "🔴 **BOT OFFLINE**")
                        await mensaje_reglas_actual.edit(content=content)
                        logger.info("✅ Mensaje marcado como OFFLINE")
                except Exception as e:
                    logger.error(f"Error editando mensaje: {e}")
                
                try:
                    await mensaje_reglas_actual.unpin()
                    logger.info("✅ Mensaje despineado")
                except Exception as e:
                    logger.error(f"Error despineando: {e}")
        
        # Limpiar Redis
        try:
            RedisState().clear_welcome_message_id(CANAL_OBJETIVO)
            logger.info("✅ Redis limpiado")
        except Exception as e:
            logger.error(f"Error limpiando Redis: {e}")
        
        logger.info("=== CLEANUP COMPLETADO ===")
        
    except Exception as e:
        logger.error(f"❌ Error en cleanup: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

def setup(bot):
    @bot.event
    async def on_ready():
        logger.info(f'=== BOT CONECTADO: {bot.user} ===')
        logger.info(f'Servidores: {len(bot.guilds)}')
        for guild in bot.guilds:
            logger.info(f'  - {guild.name} (ID: {guild.id})')
        
        logger.info("Iniciando envío de reglas...")
        success = await enviar_reglas_canal(bot)
        if success:
            logger.info("✅ SISTEMA DE REGLAS INICIALIZADO CORRECTAMENTE")
        else:
            logger.error("❌ ERROR AL INICIALIZAR SISTEMA DE REGLAS")

    @bot.event
    async def on_disconnect():
        logger.info("⚠️ BOT DESCONECTADO, ejecutando cleanup...")
        await cleanup_on_disconnect(bot)

    @bot.event
    async def on_resumed():
        logger.info("🔄 CONEXIÓN RESTABLECIDA, actualizando reglas...")
        await enviar_reglas_canal(bot)

    @bot.event
    async def on_error(event, *args, **kwargs):
        logger.error(f"❌ ERROR EN EVENTO {event}")
        logger.error(f"Args: {args}")
        logger.error(f"Traceback: {traceback.format_exc()}")

    # Comando de debugging manual
    @bot.command(name='debug_welcome')
    @commands.has_permissions(administrator=True)
    async def debug_welcome(ctx):
        """Comando para hacer debugging manual del sistema de bienvenida"""
        await ctx.send("🔍 Iniciando debugging... Revisa los logs", delete_after=5)
        
        logger.info("=== DEBUGGING MANUAL INICIADO ===")
        success = await enviar_reglas_canal(bot)
        
        if success:
            await ctx.send("✅ Debug completado - Sistema funcionando", delete_after=10)
        else:
            await ctx.send("❌ Debug completado - Se encontraron errores", delete_after=10)

    # Resto del código existente...
    @bot.event
    async def on_message(message):
        # Tu código de manejo de mensajes existente
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
            await bot.process_commands(message)
            return
        
        # [Todo tu código existente de validación aquí]
        await bot.process_commands(message)

    @bot.event
    async def on_reaction_add(reaction, user):
        # Tu código de reacciones existente
        pass
