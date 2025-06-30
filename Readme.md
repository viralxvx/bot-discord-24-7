# Discord Bot Modular con Redis para Railway

Este bot de Discord está modularizado para un mejor mantenimiento y escalabilidad. Usa Redis para gestión eficiente de estados.

## Requisitos

- Python 3.11+
- Redis (puede ser servicio externo)
- Token de Discord
- Variables de entorno configuradas

## Estructura del proyecto

- `main.py`: Punto de entrada del bot
- `config.py`: Configuraciones globales
- `redis_database.py`: Conexión y gestión Redis
- `discord_bot.py`: Instancia y configuración principal del bot
- Carpetas `commands`, `events`, `handlers`, `tasks`, `views`

## Cómo correr localmente

```bash
pip install -r requirements.txt
python main.py
