# config.py
import os # Importa el módulo os para leer variables de entorno

# ID del token de tu bot de Discord
# ¡IMPORTANTE! Ahora lee el token de la variable de entorno de Railway
BOT_TOKEN = os.getenv("DISCORD_TOKEN") 

# Si BOT_TOKEN es None, significa que la variable de entorno no se encontró.
# Esto es útil para depuración en local si no la tienes configurada.
if BOT_TOKEN is None:
    print("ADVERTENCIA: La variable de entorno DISCORD_TOKEN no está configurada. Asegúrate de que esté en Railway.")
    # Puedes poner un valor por defecto para pruebas locales si es necesario,
    # pero para producción en Railway, debería venir de la variable de entorno.
    # BOT_TOKEN = "TU_TOKEN_DE_PRUEBA_LOCAL_AQUI_SI_ES_NECESARIO"

# ID del canal objetivo para la función Go Viral (el canal donde se comparten los links)
CANAL_OBJETIVO = 1198547228876527636 # Ejemplo de ID, usa el ID real de tu canal Go Viral

# ID del canal donde se registrarán las faltas
CANAL_FALTAS = 1198906950383188048 # Ejemplo de ID, usa el ID real de tu canal de faltas

# ID del canal donde se registrarán los logs del bot (¡NUEVO!)
CANAL_LOGS = 1234567890123456789 # **REEMPLAZA ESTE CON EL ID REAL DE TU CANAL DE LOGS**

# Canal de presentacion para nuevos miembros (ID proporcionado por ti)
CANAL_PRESENTATE = 1346959710519038006 

# IDs de los canales mencionados en el mensaje de bienvenida para nuevos miembros
# ¡ESTOS SON LOS IDs QUE ME HAS PROPORCIONADO Y ESTÁN CORRECTOS!
CANAL_GUIAS_ID = 1353825076516094003 # ID del canal 📖guías
CANAL_NORMAS_GENERALES_ID = 1353821141017559103 # ID del canal ✅normas-generales
CANAL_VICTORIAS_ID = 1353823190874456085 # ID del canal 🏆victorias
CANAL_ESTRATEGIAS_PROBADAS_ID = 1376741512796442664 # ID del canal ♟estrategias-probadass
CANAL_ENTRENAMIENTO_ID = 1376209406114664559 # ID del canal 🏋️entrenamiento

# Configuración de Redis
REDIS_HOST = "localhost" # Usualmente "localhost" si Redis está en el mismo servidor
REDIS_PORT = 6379      # Puerto por defecto de Redis
REDIS_DB = 0           # Base de datos por defecto de Redis
REDIS_PASSWORD = None  # Contraseña de Redis (dejar None si no tienes)
