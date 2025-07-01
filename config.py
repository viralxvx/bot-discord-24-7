# config.py
import os 

# ID del token de tu bot de Discord
BOT_TOKEN = os.getenv("DISCORD_TOKEN") 

if BOT_TOKEN is None:
    print("ADVERTENCIA: La variable de entorno DISCORD_TOKEN no está configurada. Asegúrate de que esté en Railway.")

# ID del canal objetivo para la función Go Viral (el canal donde se comparten los links)
CANAL_OBJETIVO = 1353824447131418676 

# ID del canal donde se registrarán las faltas
CANAL_FALTAS = 1388891883551326298 

# ID del canal donde se registrarán los logs del bot
CANAL_LOGS = 1388347584061374514 # **REEMPLAZA ESTE CON EL ID REAL DE TU CANAL DE LOGS**

# Canal de presentacion para nuevos miembros
CANAL_PRESENTATE = 1346959710519038006 

# IDs de los canales mencionados en el mensaje de bienvenida para nuevos miembros
CANAL_GUIAS_ID = 1353825076516094003 
CANAL_NORMAS_GENERALES_ID = 1353821141017559103 
CANAL_VICTORIAS_ID = 1353823190874456085 
CANAL_ESTRATEGIAS_PROBADAS_ID = 1376741512796442664 
CANAL_ENTRENAMIENTO_ID = 1376209406114664559 

# Configuración de Redis
REDIS_HOST = "localhost" 
REDIS_PORT = 6379      
REDIS_DB = 0           
REDIS_PASSWORD = None
