# main.py (SOLO COPIA Y PEGA ESTA SECCIÓN, NO EL ARCHIVO ENTERO)

# ... (tus otras importaciones al inicio del archivo) ...
import config
from state_management import RedisState # Importa RedisState

# ... (el resto de tu código principal antes de la función setup_bot) ...

async def setup_bot():
    # Inicializa RedisState y adjúntala al bot
    # <--- ¡IMPORTANTE! Esta sección es la que debes ajustar
    try:
        if not config.REDIS_URL:
            raise ValueError("REDIS_URL no está configurada en config.py o en las variables de entorno.")

        bot.redis_state = RedisState(
            redis_url=config.REDIS_URL # <--- Aquí pasamos la URL completa
        )
        await bot.redis_state.connect() # Conectar a Redis
        print("Conexión a Redis establecida con éxito.")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a Redis: {e}")
        # Si la conexión a Redis es crítica, puedes decidir si quieres que el bot se detenga aquí.
        # Para este caso, es mejor que se detenga si Redis falla al inicio.
        # Considera también la posibilidad de añadir un sistema de reintentos para entornos de producción.
        return # Si Redis es crítico, salir de la función aquí.

    # Cargar Cogs (asegúrate de que esta parte ya estaba y que los cogs estén en la carpeta correcta)
    try:
        await bot.load_extension('cogs.faltas_manager')
        print("Cog 'faltas_manager' cargado.")
    except commands.ExtensionFailed as e:
        print(f"ERROR al cargar un cog: Extension 'cogs.faltas_manager' raised an error: {e}")
    except commands.ExtensionNotFound:
        print("ERROR: Cog 'cogs.faltas_manager' no encontrado.")

    try:
        await bot.load_extension('cogs.inactivity_tracker')
        print("Cog 'inactivity_tracker' cargado.")
    except commands.ExtensionFailed as e:
        print(f"ERROR al cargar un cog: Extension 'cogs.inactivity_tracker' raised an error: {e}")
    except commands.ExtensionNotFound:
        print("ERROR: Cog 'cogs.inactivity_tracker' no encontrado.")

    try:
        await bot.load_extension('cogs.support_proroga')
        print("Cog 'support_proroga' cargado.")
    except commands.ExtensionFailed as e:
        print(f"ERROR al cargar un cog: Extension 'cogs.support_proroga' raised an error: {e}")
    except commands.ExtensionNotFound:
        print("ERROR: Cog 'cogs.support_proroga' no encontrado.")

# ... (el resto de tu archivo main.py) ...
# Asegúrate de que al final de tu main.py, la ejecución sea:
# if __name__ == "__main__":
#    import asyncio
#    asyncio.run(main())
