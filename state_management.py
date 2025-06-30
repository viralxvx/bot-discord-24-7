import datetime
from redis_database import cargar_estado, guardar_estado

# Variables globales que se usarán en todo el bot
estado = cargar_estado()

faltas_dict = estado["faltas_dict"]
amonestaciones = estado["amonestaciones"]
ultima_publicacion_dict = estado["ultima_publicacion_dict"]
permisos_inactividad = estado["permisos_inactividad"]
baneos_temporales = estado["baneos_temporales"]
mensajes_recientes = estado["mensajes_recientes"]
active_conversations = estado["active_conversations"]

# Constantes para mantener un límite de memoria y control de tiempos
MAX_MENSAJES_RECIENTES = 20
INACTIVITY_TIMEOUT = 300  # segundos (5 minutos)

# Función para guardar el estado completo en Redis
def save_state():
    guardar_estado(
        faltas_dict,
        amonestaciones,
        ultima_publicacion_dict,
        permisos_inactividad,
        baneos_temporales,
        mensajes_recientes,
        active_conversations
    )

# Función para obtener la hora actual en UTC
def now():
    return datetime.datetime.now(datetime.timezone.utc)
