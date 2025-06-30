import datetime
import re
import discord

def is_valid_x_url(url: str) -> bool:
    """Valida si la URL cumple el patrón esperado de https://x.com/usuario/status/id"""
    pattern = r"https://x\.com/[^/]+/status/\d+"
    return bool(re.match(pattern, url))

def normalize_message(content: str) -> str:
    """Normaliza un mensaje para comparaciones (quita espacios y pasa a minúsculas)"""
    return content.strip().lower()

def get_current_utc_time():
    """Devuelve la fecha y hora actual en UTC"""
    return datetime.datetime.now(datetime.timezone.utc)

def mention_user(user: discord.User) -> str:
    """Devuelve la mención de un usuario"""
    return user.mention

def format_ticket_id(counter: int) -> str:
    """Formatea el ID del ticket con ceros a la izquierda"""
    return f"ticket-{counter:03d}"
