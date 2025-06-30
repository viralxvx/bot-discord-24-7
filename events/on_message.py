import discord
from handlers.faltas import actualizar_mensaje_faltas
from utils import registrar_log, faltas_dict

CANAL_FALTAS = "📤faltas"
CANAL_PRESENTATE = "👉preséntate"

async def on_member_join(member):
    canal_presentate = discord.utils.get(member.guild.text_channels, name=CANAL_PRESENTATE)
    canal_faltas = discord.utils.get(member.guild.text_channels, name=CANAL_FALTAS)

    if canal_presentate:
        try:
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
        except discord.Forbidden:
            pass

    if canal_faltas:
        try:
            if member.id not in faltas_dict:
                faltas_dict[member.id] = {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None}
            await actualizar_mensaje_faltas(canal_faltas, member, 0, 0, "OK")
        except discord.Forbidden:
            pass

    await registrar_log(f"👤 Nuevo miembro: {member.name}", categoria="miembros")
