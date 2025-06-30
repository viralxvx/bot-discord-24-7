import os
import json
import datetime
from collections import defaultdict
from config import STATE_FILE

# Usar /data para persistencia en Railway
PERSISTENT_STATE_PATH = "/data/state.json"

# Variables globales para el estado
ultima_publicacion_dict = defaultdict(lambda: datetime.datetime.now(datetime.timezone.utc))
amonestaciones = defaultdict(list)
baneos_temporales = defaultdict(lambda: None)
permisos_inactividad = defaultdict(lambda: None)
ticket_counter = 0
active_conversations = {}
faq_data = {}
faltas_dict = defaultdict(lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None})
mensajes_recientes = defaultdict(list)

def load_state():
    global ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, ticket_counter, active_conversations, faq_data, faltas_dict, mensajes_recientes
    
    # Elegir la ruta del archivo de estado
    state_file = STATE_FILE
    if os.path.exists(PERSISTENT_STATE_PATH):
        state_file = PERSISTENT_STATE_PATH
    
    try:
        with open(state_file, "r") as f:
            state = json.load(f)
        
        # Función para cargar datetime
        def load_datetime(dt_str):
            if dt_str is None:
                return None
            dt = datetime.datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        
        # Cargar cada variable
        ultima_publicacion_dict = defaultdict(
            lambda: datetime.datetime.now(datetime.timezone.utc),
            {k: load_datetime(v) for k, v in state.get("ultima_publicacion_dict", {}).items()}
        )
        
        amonestaciones = defaultdict(
            list, 
            {k: [load_datetime(t) for t in v] for k, v in state.get("amonestaciones", {}).items()}
        )
        
        baneos_temporales = defaultdict(
            lambda: None,
            {k: load_datetime(v) for k, v in state.get("baneos_temporales", {}).items()}
        )
        
        permisos_inactividad = defaultdict(
            lambda: None,
            {k: {"inicio": load_datetime(v["inicio"]), "duracion": v["duracion"]} if v else None 
             for k, v in state.get("permisos_inactividad", {}).items()}
        )
        
        ticket_counter = state.get("ticket_counter", 0)
        active_conversations = state.get("active_conversations", {})
        faq_data = state.get("faq_data", {})
        
        faltas_dict = defaultdict(
            lambda: {"faltas": 0, "aciertos": 0, "estado": "OK", "mensaje_id": None, "ultima_falta_time": None},
            {
                k: {
                    "faltas": v["faltas"],
                    "aciertos": v["aciertos"],
                    "estado": v["estado"],
                    "mensaje_id": v["mensaje_id"],
                    "ultima_falta_time": load_datetime(v["ultima_falta_time"]) if v["ultima_falta_time"] else None
                } for k, v in state.get("faltas_dict", {}).items()
            }
        )
        
        mensajes_recientes = defaultdict(list, state.get("mensajes_recientes", {}))
        
    except FileNotFoundError:
        # Mantener valores por defecto si no existe el archivo
        pass
    except json.JSONDecodeError:
        # Archivo corrupto, se reiniciará el estado
        pass

def save_state():
    # Guardar siempre en la ruta persistente
    state_file = PERSISTENT_STATE_PATH
    
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
    
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(state, f)
    except Exception as e:
        # Fallback a la ruta local si hay error
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
        except:
            print(f"No se pudo guardar el estado: {str(e)}")

# Cargar estado al importar
load_state()
