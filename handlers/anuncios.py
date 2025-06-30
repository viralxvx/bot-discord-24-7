import discord
from handlers.logs import registrar_log

async def handle_anuncios(bot: discord.Client, message: discord.Message):
    try:
        log_msg = f"📢 Anuncio publicado por {message.author.name}: {message.content[:100]}"
        await registrar_log(log_msg, categoria="anuncios")
    except Exception as e:
        print(f"[ERROR] al manejar anuncio: {e}")
