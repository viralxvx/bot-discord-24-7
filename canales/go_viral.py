import discord
from discord.ext import commands
import re
import asyncio
from state_management import RedisState
from canales.logs import registrar_log
from canales.faltas import registrar_falta, enviar_advertencia
from config import CANAL_OBJETIVO, CANAL_LOGS

async def enviar_reglas_canal(bot):
    """Envía y fija las reglas optimizadas en el canal objetivo"""
    canal = bot.get_channel(CANAL_OBJETIVO)
    if not canal:
        print(f"❌ Canal objetivo {CANAL_OBJETIVO} no encontrado")
        return False

    # Mensaje optimizado (cumple con límite de 2000 caracteres)
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

*Bot 24/7 • Sistema automatizado • Apoyo mutuo*"""
    
    try:
        # Verificar longitud
        if len(mensaje_reglas) > 2000:
            print(f"❌ Mensaje excede límite de Discord ({len(mensaje_reglas)}/2000)")
            return False

        # Limpiar reglas anteriores del bot
        deleted = 0
        async for message in canal.history(limit=30):
            if message.author == bot.user and "REGLAS GO-VIRAL" in message.content:
                try:
                    await message.unpin()
                except:
                    pass
                await message.delete()
                deleted += 1
                await asyncio.sleep(1.2)  # Prevenir rate limits
        print(f"♻️ Eliminadas {deleted} reglas anteriores")

        # Enviar y fijar nuevas reglas
        mensaje_enviado = await canal.send(mensaje_reglas)
        await mensaje_enviado.pin(reason="Reglas actualizadas Go-Viral")
        
        # Registrar en logs
        await registrar_log(
            f"Reglas go-viral publicadas y fijadas ({len(mensaje_reglas)} caracteres)", 
            bot.user, 
            canal
        )
        return True
        
    except discord.Forbidden:
        print("❌ Error de permisos: Verificar 'Enviar Mensajes', 'Gestionar Mensajes' y 'Fijar Mensajes'")
    except Exception as e:
        print(f"❌ Error crítico: {type(e).__name__} - {e}")
    return False

def setup(bot):
    @bot.event
    async def on_ready():
        print(f'✅ {bot.user} conectado!')
        await enviar_reglas_canal(bot)

    @bot.event
    async def on_message(message):
        if message.channel.id != CANAL_OBJETIVO or message.author.bot:
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
                await enviar_notificacion_temporal(
                    message.channel, 
                    message.author, 
                    f"{message.author.mention} **Error:** URL inválida. Usa formato: `https://x.com/usuario/status/123456...`"
                )
                await registrar_falta(message.author, "URL inválida", message.channel)
                await registrar_log("Mensaje eliminado: URL inválida", message.author, message.channel)
                return

        # Verificar intervalo de publicaciones
        redis_state = RedisState()
        last_post = redis_state.get_last_post(message.author.id)
        recent_posts = redis_state.get_recent_posts(CANAL_OBJETIVO)
        
        if last_post and len([p for p in recent_posts if p['author_id'] != message.author.id]) < 2:
            await message.delete()
            await enviar_notificacion_temporal(
                message.channel,
                message.author,
                f"{message.author.mention} **Error:** Espera al menos 2 publicaciones de otros antes de publicar nuevamente."
            )
            await registrar_falta(message.author, "Publicación prematura", message.channel)
            await registrar_log("Mensaje eliminado: Intervalo no respetado", message.author, message.channel)
            return

        # Verificar reacciones 🔥 en publicaciones previas
        required_reactions = redis_state.get_required_reactions(message.author.id, CANAL_OBJETIVO)
        if not all(redis_state.has_reaction(message.author.id, post_id) for post_id in required_reactions):
            await message.delete()
            await enviar_notificacion_temporal(
                message.channel,
                message.author,
                f"{message.author.mention} **Error:** Reacciona con 🔥 a TODAS las publicaciones posteriores a tu última."
            )
            await registrar_falta(message.author, "Falta de reacciones 🔥", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacciones 🔥", message.author, message.channel)
            return

        # Corregir URL si es necesario
        if corrected_url:
            await message.delete()
            new_message = await message.channel.send(f"{corrected_url} (Corregido por el bot)")
            await registrar_log(f"URL corregida: {content} -> {corrected_url}", message.author, message.channel)
            await enviar_notificacion_temporal(
                message.channel,
                message.author,
                f"{message.author.mention} **URL corregida:** Usa formato limpio `https://x.com/usuario/status/123456...`"
            )
            message = new_message

        # Guardar publicación en Redis
        redis_state.save_post(message.id, message.author.id, CANAL_OBJETIVO)

        # Esperar reacción 👍 del autor
        def check_reaction(reaction, user):
            return (user == message.author 
                    and str(reaction.emoji) == '👍' 
                    and reaction.message.id == message.id)

        try:
            await bot.wait_for('reaction_add', timeout=120, check=check_reaction)
        except asyncio.TimeoutError:
            await message.delete()
            await enviar_notificacion_temporal(
                message.channel,
                message.author,
                f"{message.author.mention} **Error:** No reaccionaste con 👍 en 120 segundos."
            )
            await registrar_falta(message.author, "Sin reacción 👍", message.channel)
            await registrar_log("Mensaje eliminado: Sin reacción 👍", message.author, message.channel)

        await bot.process_commands(message)

    @bot.event
    async def on_reaction_add(reaction, user):
        if reaction.message.channel.id != CANAL_OBJETIVO or user.bot:
            return

        # Prohibir 🔥 en propia publicación
        if str(reaction.emoji) == '🔥' and user == reaction.message.author:
            await reaction.remove(user)
            await enviar_notificacion_temporal(
                reaction.message.channel,
                user,
                f"{user.mention} **Error:** No puedes reaccionar con 🔥 a tu propia publicación."
            )
            await registrar_falta(user, "Auto-reacción 🔥", reaction.message.channel)
            await registrar_log("Reacción eliminada: 🔥 en propia publicación", user, reaction.message.channel)

        # Registrar reacción 🔥 válida
        if str(reaction.emoji) == '🔥' and user != reaction.message.author:
            RedisState().save_reaction(user.id, reaction.message.id)

    async def enviar_notificacion_temporal(channel, user, content):
        """Envía notificación temporal (15s) y DM con falta"""
        try:
            msg = await channel.send(content)
            await asyncio.sleep(15)
            await msg.delete()
        except:
            pass
        
        try:
            await user.send(f"⚠️ **Falta detectada:** {content.replace(user.mention, '').strip()}")
        except discord.Forbidden:
            print(f"❌ No se pudo enviar DM a {user.name}")
