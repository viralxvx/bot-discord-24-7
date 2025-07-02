# config.py

import os

# --- Configuración del Bot ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# --- IDs de Canales (¡REEMPLAZA ESTOS VALORES CON LAS IDs REALES DE TU SERVIDOR!) ---
CANAL_GO_VIRAL_ID = 1353824447131418676 # El canal donde los usuarios publican (GoViral)
CANAL_FALTAS_ID = 1388891883551326298   # El canal donde se mostrarán las tarjetas de faltas
CANAL_SOPORTE_ID = 333333333333333333  # El canal donde se solicitarán las prórrogas (soporte)
CANAL_LOGS_ID = 1388347584061374514     # Canal para logs internos del bot

# --- IDs de Roles (¡REEMPLAZA ESTOS VALORES!) ---
ROLE_MODERADOR_ID = 1389761947062505502 # ID del rol de Moderador para aprobar prórrogas
# Puedes añadir más roles si es necesario para diferentes permisos

# --- Configuración de Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# --- Reglas de Inactividad ---
DIAS_INACTIVIDAD_PARA_BAN = 3      # Días sin publicar para el primer baneo
DURACION_BAN_DIAS = 7              # Duración del baneo temporal en días

# --- Reglas de Prórrogas ---
MAX_PRORROGA_DAYS = 30             # Duración máxima de una prórroga en días
DIAS_PRE_AVISO_PRORROGA = 2        # Días antes de expirar una prórroga para enviar un DM de aviso

# --- Mensaje Fijo del Canal #faltas (ID del mensaje) ---
# Si quieres un mensaje fijo en la parte superior del canal #faltas (ej. un título/descripción),
# el bot intentará encontrarlo. Si no lo encuentra, lo creará y guardará su ID aquí.
# Si lo dejas en None, el bot no gestionará un mensaje fijo.
FALTAS_PANEL_MESSAGE_ID = None # Se actualizará dinámicamente o lo puedes fijar si ya existe
FALTAS_PANEL_CONTENT = (
    "**__Panel de Control de Actividad GoViral__**\n"
    "Este canal muestra el estado de actividad y el historial de faltas de los miembros de la comunidad GoViral.\n"
    "Cada mensaje es una 'tarjeta' de usuario que se actualiza automáticamente. "
    "Los usuarios expulsados son eliminados de este panel.\n\n"
    "✅ = Activo | ⚠️ = Falta Menor | ⏳ = Prórroga | ⛔️ = Baneado | ❌ = Expulsado (eliminado del panel)\n\n"
    "--- (Las tarjetas de usuario aparecerán debajo de este mensaje) ---"
)

# --- Mensaje Fijo del Canal #soporte (ID del mensaje) ---
# ID del mensaje que contendrá el menú desplegable de soporte.
# El bot lo creará o lo recuperará en el inicio.
SOPORTE_MENU_MESSAGE_ID = None # Se actualizará dinámicamente
SOPORTE_MENU_CONTENT = (
    "👋 **Bienvenido al Centro de Soporte de GoViral!**\n\n"
    "Aquí puedes realizar diversas gestiones y solicitudes. "
    "Usa el menú desplegable a continuación para elegir la opción que necesites:\n\n"
)
