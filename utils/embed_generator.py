# utils/embed_generator.py

import discord
from datetime import datetime
import time

def get_current_timestamp():
    """Retorna el timestamp actual en segundos."""
    return time.time()

def format_timestamp(timestamp: float) -> str:
    """Formatea un timestamp flotante a una cadena de fecha y hora legible."""
    if not timestamp:
        return "N/A"
    return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S AST")

def create_fault_card_embed(
    user: discord.Member,
    status: str, # "activo", "baneado", "expulsado", "prorroga", "falta_menor"
    last_post_time: float = 0.0,
    inactivity_ban_start: float = 0.0,
    inactivity_extension_end: float = 0.0,
    proroga_reason: str = "No especificada",
    faults_history: list = None # Lista de tuplas/diccionarios de faltas recientes
) -> discord.Embed:
    """
    Crea o actualiza el embed de la tarjeta de faltas de un usuario.
    """
    if faults_history is None:
        faults_history = []

    embed = discord.Embed(timestamp=datetime.now())
    embed.set_footer(text=f"ID de Usuario: {user.id}")

    # Definir título y color según el estado
    if status == "prorroga":
        embed.title = f"⏳ Historial de @{user.display_name}"
        embed.color = discord.Color.purple()
        estado_desc = f"Activo (con prórroga de inactividad)"
    elif status == "baneado":
        embed.title = f"⛔️ Historial de @{user.display_name}"
        embed.color = discord.Color.orange()
        estado_desc = f"BANEADO del servidor por inactividad"
    elif status == "expulsado": # Esto solo para la lógica interna, la tarjeta se borrará
        embed.title = f"❌ Historial de @{user.display_name}"
        embed.color = discord.Color.red()
        estado_desc = f"EXPULSADO del servidor por inactividad recurrente"
    elif status == "falta_menor":
        embed.title = f"⚠️ Historial de @{user.display_name}"
        embed.color = discord.Color.blue()
        estado_desc = f"Activo, con faltas menores"
    else: # "activo" o "none"
        embed.title = f"✅ Historial de @{user.display_name}"
        embed.color = discord.Color.green()
        estado_desc = f"Activo y Participativo"
    
    embed.description = f"Estado actual: **{estado_desc}**"

    # Campos Generales
    embed.add_field(name="Última Publicación Válida", value=format_timestamp(last_post_time), inline=False)

    # Campos específicos según el estado
    if status == "prorroga":
        embed.add_field(name="Prórroga Válida Hasta", value=format_timestamp(inactivity_extension_end), inline=False)
        embed.add_field(name="Razón Declarada", value=proroga_reason, inline=False)
    elif status == "baneado":
        embed.add_field(name="Inicio del Baneo", value=format_timestamp(inactivity_ban_start), inline=False)
        embed.add_field(name="Fin del Baneo", value=format_timestamp(inactivity_ban_start + 86400 * 7), inline=False) # 7 días
        embed.add_field(name="Próxima Consecuencia", value="Expulsión si vuelve a ser inactivo tras desban", inline=False)
    elif status == "expulsado":
        embed.add_field(name="Tipo de Expulsión", value="Inactividad recurrente tras baneo previo", inline=False)
    
    # Historial de faltas (solo para faltas menores, las de inactividad se ven en el estado)
    if faults_history:
        history_str = "\n".join([f"• {format_timestamp(f['timestamp'])}: {f['reason']}" for f in faults_history])
        embed.add_field(name="Faltas Registradas Recientes", value=history_str if history_str else "Ninguna", inline=False)
    else:
        # Solo mostrar si el usuario no tiene historial reciente y no está en un estado de falta evidente
        if status in ["activo", "falta_menor"]: # No mostrar "ninguna" si ya está baneado etc.
            embed.add_field(name="Faltas Registradas", value="Ninguna", inline=False)

    return embed

def create_proroga_request_embed(
    user: discord.Member,
    reason: str,
    duration_str: str,
    status: str = "PENDIENTE", # PENDIENTE, APROBADA, DENEGADA
    moderator: discord.Member = None,
    approved_until: float = 0.0
) -> discord.Embed:
    """
    Crea el embed para la solicitud de prórroga en el canal de soporte para moderadores.
    """
    embed = discord.Embed(timestamp=datetime.now())
    embed.set_author(name=f"Solicitud de Prórroga de {user.display_name}", icon_url=user.avatar.url if user.avatar else discord.Embed.Empty)
    embed.add_field(name="Usuario Solicitante", value=f"{user.mention} (ID: {user.id})", inline=False)
    embed.add_field(name="Razón Declarada", value=reason, inline=False)
    embed.add_field(name="Duración Solicitada", value=duration_str if duration_str else "No especificada", inline=False)

    if status == "PENDIENTE":
        embed.title = "⏰ Nueva Solicitud de Prórroga"
        embed.color = discord.Color.orange()
    elif status == "APROBADA":
        embed.title = "✅ Solicitud de Prórroga Aprobada"
        embed.color = discord.Color.green()
        embed.add_field(name="Aprobada por", value=moderator.mention if moderator else "N/A", inline=True)
        embed.add_field(name="Válida Hasta", value=format_timestamp(approved_until), inline=True)
    elif status == "DENEGADA":
        embed.title = "❌ Solicitud de Prórroga Denegada"
        embed.color = discord.Color.red()
        embed.add_field(name="Denegada por", value=moderator.mention if moderator else "N/A", inline=False)
    
    embed.set_footer(text=f"Estado: {status}")
    return embed
