# mensajes/anuncios_texto.py

import discord
from datetime import datetime
import hashlib

LOGO_URL = "https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj"

def EMBED_ANUNCIO_TEMPLATE(tipo, titulo, descripcion, url, autor, fecha, logo_url):
    embed = discord.Embed(
        title=f"📢 {titulo} — ¡Nuevo!",
        description=f"{descripcion}\n\n[Haz clic aquí para ver la actualización]({url})",
        color=0x0057b8 if tipo == "Normas Generales" else 0xf1c40f
    )
    embed.set_thumbnail(url=logo_url)
    embed.add_field(name="Tipo", value=tipo, inline=True)
    embed.add_field(name="Fecha", value=fecha.strftime('%d/%m/%Y'), inline=True)
    embed.set_footer(text=f"Publicado por {autor} | VXbot")
    return embed

def EMBED_RESUMEN_REINGRESO(member, novedades, logo_url):
    desc = (
        f"¡Bienvenido de vuelta, {member.mention}!\n\n"
        f"Durante tu ausencia hemos tenido novedades importantes:\n"
    )
    for nov in novedades:
        desc += f"• **{nov['titulo']}** — [Ver]({nov['url']})\n"
    desc += "\nPuedes ver el historial completo usando `/novedades`."
    embed = discord.Embed(
        title="🆕 Resumen de Novedades",
        description=desc,
        color=0x0057b8
    )
    embed.set_thumbnail(url=logo_url)
    embed.set_footer(text="VXbot — Tu comunidad evoluciona, tú también.")
    return embed

TITULO_NORMAS = "Actualización de Normas Generales"
DESC_NORMAS = "¡Se han actualizado las normas generales del servidor! Haz clic para conocer las nuevas reglas."
URL_NORMAS = "https://discord.com/channels/{GUILD_ID}/{CANAL_NORMAS}/{MESSAGE_ID}"

TITULO_FUNCION = "Nueva Funcionalidad Disponible"
DESC_FUNCION = "¡Lanzamos una nueva función en el sistema! Descubre cómo sacarle provecho."
URL_FUNCION = "https://discord.com/channels/{GUILD_ID}/{CANAL_FUNCIONES}/{MESSAGE_ID}"

def get_update_id_normas():
    texto = DESC_NORMAS  # O el texto real de normas
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def get_update_id_funcion():
    texto = DESC_FUNCION  # O el texto real de la función nueva
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()
