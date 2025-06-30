# main.py
import asyncio
import os
from dotenv import load_dotenv
import logging

load_dotenv()  # Carga las variables del archivo .env

from discord_bot import bot  # Importa la instancia del bot correctamente creada en bot_instance.py
from redis_database import redis_client  # Cliente Redis (asumiendo que está bien definido)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("⚠️ No se encontró la variable de entorno TOKEN")

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        logging.info("Iniciando bot...")
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        logging.info("Bot detenido manualmente")
    finally:
        await bot.close()
        # Cierra la conexión de Redis si existe y tiene método close (soporta await)
        if redis_client and hasattr(redis_client, "close"):
            close_coro = redis_client.close()
            if asyncio.iscoroutine(close_coro):
                await close_coro
        logging.info("Conexiones cerradas")

if __name__ == "__main__":
    asyncio.run(main())
