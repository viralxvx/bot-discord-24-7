import asyncio
import os
from dotenv import load_dotenv
from discord_bot import bot  # Instancia principal del bot
from redis_database import redis_client  # Cliente Redis
import logging

load_dotenv()  # Carga variables de entorno desde .env

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("⚠️ No se encontró la variable de entorno DISCORD_TOKEN")

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        logging.info("Iniciando bot...")
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        logging.info("Bot detenido manualmente")
    finally:
        await bot.close()
        if redis_client:
            await redis_client.close()
        logging.info("Conexiones cerradas")

if __name__ == "__main__":
    asyncio.run(main())
