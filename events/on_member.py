import discord
from config import CANAL_FALTAS
from state_management import faltas_dict
from utils import actualizar_mensaje_faltas, registrar_log

async def handle_member_join(member):
    try:
        canal_presentate = discord.utils.get(member.guild.text_channels, name="👉preséntate")
        canal_faltas = discord.utils.get(member.guild.text_channels, name=CANAL_FALTAS)
        
        if canal_presentate:
            mensaje = (
                f"👋 **¡Bienvenid@ a VX {member.mention}!**\n\n"
                "**Sigue estos pasos**:\n"
                "📖 Lee las 3 guías\n"
                "✅ Revisa las normas\n"
                "🏆 Mira las victorias\n"
                "♟ Estudia las estrategias\n"
                "🏋 Luego solicita ayuda para tu primer post.\n\n"
                "📤 **Revisa tu estado** en #📤faltas para mantenerte al día.\n"
                "🚫 **Mensajes repetidos** serán eliminados en todos los canales (excepto #📝logs).\n"
                "⏳ Usa `!permiso <días>` en #⛔reporte-de-incumplimiento para pausar la obligación de publicar (máx. 7 días)."
            )
            await canal_presentate.send(mensaje)
                
        if canal_faltas:
            if member.id not in faltas_dict:
                faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
            await actualizar_mensaje_faltas(canal_faltas, member, 0, 0, "OK")
                
        await registrar_log(f"👤 Nuevo miembro: {member.name}", categoria="miembros")
    except Exception as e:
        print(f"Error en on_member_join: {str(e)}")

async def handle_member_remove(member):
    try:
        await registrar_log(f"👋 Miembro salió: {member.name}", categoria="miembros")
    except Exception as e:
        print(f"Error en on_member_remove: {str(e)}")
