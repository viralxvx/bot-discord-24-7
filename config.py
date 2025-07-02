# config.py

import os

# --- Configuración del Bot ---
# El token de tu bot de Discord. Se obtiene de las variables de entorno de Railway
# (donde lo tienes configurado como "DISCORD_TOKEN").
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# --- IDs de Canales ---
CANAL_GO_VIRAL_ID = 1353824447131418676 # El canal donde los usuarios publican contenido (GoViral)
CANAL_FALTAS_ID = 1388891883551326298  # El canal donde se mostrarán las tarjetas de faltas de los usuarios
CANAL_SOPORTE_ID = 1376744723665911894  # El canal donde se solicitarán las prórrogas (soporte)
CANAL_LOGS_ID = 1388347584061374514    # Canal para registros (logs) internos del bot y notificaciones importantes

# --- IDs de Roles ---
ROLE_MODERADOR_ID = 1389761947062505502 # ID del rol de Moderador/Administrador para aprobar/denegar solicitudes de prórrogas

# --- Configuración de Redis ---
# La URL de conexión a tu base de datos Redis. Se obtiene de las variables de entorno de Railway
# (donde la tienes configurada como "REDIS_URL").
REDIS_URL = os.getenv("REDIS_URL")

# --- Configuración del Sistema Go Viral ---
# ¡ESTAS SON LAS LÍNEAS QUE FALTABAN O ESTABAN MAL!
MIN_REACCIONES_GO_VIRAL = 5           # Número de reacciones únicas necesarias para volverse viral (puedes ajustar este valor)
TIEMPO_ESPERA_POST_MINUTOS = 24 * 60  # 24 horas en minutos (tiempo de espera entre posts del mismo usuario)

# --- Reglas de Inactividad ---
DIAS_INACTIVIDAD_PARA_BAN = 3      # Número de días sin publicar para que un usuario reciba su primer baneo temporal
DURACION_BAN_DIAS = 7              # Duración del baneo temporal en días (ej. 7 para 7 días)

# --- Reglas de Prórrogas ---
MAX_PRORROGA_DAYS = 30             # Duración máxima que un usuario puede solicitar para una prórroga en días
DIAS_PRE_AVISO_PRORROGA = 2        # Días antes de que expire una prórroga para enviar un mensaje directo (DM) de aviso al usuario

# --- Contenido y ID del Mensaje Fijo del Canal #faltas ---
# El bot intentará encontrar este mensaje. Si no lo encuentra, lo creará y guardará su ID aquí.
# Si lo dejas en None, el bot gestionará la creación automáticamente.
FALTAS_PANEL_MESSAGE_ID = None # Se actualizará dinámicamente una vez creado por el bot
FALTAS_PANEL_CONTENT = (
    "**__Panel de Control de Actividad GoViral__**\n"
    "Este canal muestra el estado de actividad y el historial de faltas de los miembros de la comunidad GoViral.\n"
    "Cada mensaje es una 'tarjeta' de usuario que se actualiza automáticamente. "
    "Los usuarios expulsados son eliminados de este panel.\n\n"
    "✅ = Activo | ⚠️ = Falta Menor | ⏳ = Prórroga | ⛔️ = Baneado | ❌ = Expulsado (eliminado del panel)\n\n"
    "--- (Las tarjetas de usuario aparecerán debajo de este mensaje) ---"
)

# --- Contenido y ID del Mensaje Fijo del Canal #soporte ---
# El bot creará o recuperará este mensaje al iniciar.
SOPORTE_MENU_MESSAGE_ID = None # Se actualizará dinámicamente una vez creado por el bot
SOPORTE_MENU_CONTENT = (
    "👋 **Bienvenido al Centro de Soporte de GoViral!**\n\n"
    "Aquí puedes realizar diversas gestiones y solicitudes. "
    "Usa el menú desplegable a continuación para elegir la opción que necesites:\n\n"
)
