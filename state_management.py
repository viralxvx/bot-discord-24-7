from collections import defaultdict
import datetime
import json

# Estado persistente (globales)
ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
amonestaciones = defaultdict(list)
baneos_temporales = defaultdict(lambda: None)
permisos_inactividad = defaultdict(lambda: None)
ticket_counter = 0
active_conversations = {}
faq_data = {}
faltas_dict = defaultdict(lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None})
mensajes_recientes = defaultdict(list)

STATE_FILE = "state.json"

def save_state():
    state = {
        "ultima_publicacion_dict": {str(k): v.isoformat() for k, v in ultima_publicacion_dict.items()},
        "amonestaciones": {str(k): [t.isoformat() for t in v] for k, v in amonestaciones.items()},
        "baneos_temporales": {str(k): v.isoformat() if v else None for k, v in baneos_temporales.items()},
        "permisos_inactividad": {str(k): {"inicio": v["inicio"].isoformat(), "duracion": v["duracion"]} if v else None for k, v in permisos_inactividad.items()},
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
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
