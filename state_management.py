from redis_database import save_state, load_state

# Claves para guardar distintos estados
KEY_FALTAS = "bot:faltas_dict"
KEY_AMONESTACIONES = "bot:amonestaciones"
KEY_PERMISOS = "bot:permisos_inactividad"
KEY_BANEOS = "bot:baneos_temporales"
KEY_ULTIMA_PUBLICACION = "bot:ultima_publicacion_dict"
KEY_ACTIVE_CONVERSATIONS = "bot:active_conversations"
KEY_MENSAJES_RECIENTES = "bot:mensajes_recientes"
KEY_TICKET_COUNTER = "bot:ticket_counter"

def save_all_states(bot_state):
    """
    Guarda todos los estados en Redis usando el diccionario bot_state
    """
    save_state(KEY_FALTAS, bot_state.get("faltas_dict", {}))
    save_state(KEY_AMONESTACIONES, bot_state.get("amonestaciones", {}))
    save_state(KEY_PERMISOS, bot_state.get("permisos_inactividad", {}))
    save_state(KEY_BANEOS, bot_state.get("baneos_temporales", {}))
    save_state(KEY_ULTIMA_PUBLICACION, bot_state.get("ultima_publicacion_dict", {}))
    save_state(KEY_ACTIVE_CONVERSATIONS, bot_state.get("active_conversations", {}))
    save_state(KEY_MENSAJES_RECIENTES, bot_state.get("mensajes_recientes", {}))
    save_state(KEY_TICKET_COUNTER, bot_state.get("ticket_counter", 0))

def load_all_states():
    """
    Carga todos los estados desde Redis y devuelve un diccionario con ellos
    """
    return {
        "faltas_dict": load_state(KEY_FALTAS, {}),
        "amonestaciones": load_state(KEY_AMONESTACIONES, {}),
        "permisos_inactividad": load_state(KEY_PERMISOS, {}),
        "baneos_temporales": load_state(KEY_BANEOS, {}),
        "ultima_publicacion_dict": load_state(KEY_ULTIMA_PUBLICACION, {}),
        "active_conversations": load_state(KEY_ACTIVE_CONVERSATIONS, {}),
        "mensajes_recientes": load_state(KEY_MENSAJES_RECIENTES, {}),
        "ticket_counter": load_state(KEY_TICKET_COUNTER, 0),
    }
