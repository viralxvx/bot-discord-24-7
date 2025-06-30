import datetime
import json
from collections import defaultdict
from redis_database import load_state, save_state as redis_save_state

# Cargar estado inicial desde Redis
state_data = load_state() or {}

# Variables globales para el estado
ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
amonestaciones = defaultdict(list)
baneos_temporales = defaultdict(lambda: None)
permisos_inactividad = defaultdict(lambda: None)
ticket_counter = 0
active_conversations = {}
faq_data = state_data.get("faq_data", {})
faltas_dict = defaultdict(
    lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None},
    state_data.get("faltas_dict", {})
)
mensajes_recientes = defaultdict(list, state_data.get("mensajes_recientes", {}))

def save_state():
    """Guardar estado actual en Redis"""
    state = {
        "ultima_publicacion_dict": {str(k): v.isoformat() for k, v in ultima_publicacion_dict.items()},
        "amonestaciones": {str(k): [t.isoformat() for t in v] for k, v in amonestaciones.items()},
        "baneos_temporales": {str(k): v.isoformat() if v else None for k, v in baneos_temporales.items()},
        "permisos_inactividad": {str(k): {"inicio": v["inicio"].isoformat(), "duracion": v["duracion"]} if v else None 
                                for k, v in permisos_inactividad.items()},
        "ticket_counter": ticket_counter,
        "active_conversations": active_conversations,
        "faq_data": faq_data,
        "faltas_dict": {
            str(k): {
                "faltas": v["faltas"],
                "aciertos": v["aciertos"],
                "estado": v["estado"],
                "mensaje_id": v["mensaje_id"],
                "ultima_falta_time": v["ultima_falta_time"].isoformat() if v["ultima_falta_time"] else None
            } for k, v in faltas_dict.items()
        },
        "mensajes_recientes": {str(k): v for k, v in mensajes_recientes.items()}
    }
    
    return redis_save_state(state)

# Registrar guardado de estado al salir
import atexit
atexit.register(save_state)
