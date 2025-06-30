from .config import Session, last_save_time, SAVE_STATE_DELAY
import time
import datetime

# Estado global
ultima_publicacion_dict = {}
amonestaciones = {}
baneos_temporales = {}
permisos_inactividad = {}
ticket_counter = 0
active_conversations = {}
faq_data = {}
faltas_dict = {}
mensajes_recientes = {}

def load_state():
    global ultima_publicacion_dict, amonestaciones, baneos_temporales, permisos_inactividad, ticket_counter, active_conversations, faq_data, faltas_dict, mensajes_recientes
    session = Session()
    try:
        state = session.query(State).first()
        if state:
            ultima_publicacion_dict = {int(k): datetime.datetime.fromisoformat(v) for k, v in state.ultima_publicacion_dict.items()} if state.ultima_publicacion_dict else {}
            amonestaciones = {int(k): [datetime.datetime.fromisoformat(t) for t in v] for k, v in state.amonestaciones.items()} if state.amonestaciones else {}
            baneos_temporales = {int(k): datetime.datetime.fromisoformat(v) if v else None for k, v in state.baneos_temporales.items()} if state.baneos_temporales else {}
            permisos_inactividad = {int(k): {"inicio": datetime.datetime.fromisoformat(v["inicio"]), "duracion": v["duracion"]} if v else None for k, v in state.permisos_inactividad.items()} if state.permisos_inactividad else {}
            ticket_counter = state.ticket_counter or 0
            active_conversations = state.active_conversations or {}
            faq_data = state.faq_data or {}
            faltas_dict = {int(k): v for k, v in state.faltas_dict.items()} if state.faltas_dict else {}
            mensajes_recientes = {int(k): v for k, v in state.mensajes_recientes.items()} if state.mensajes_recientes else {}
        else:
            ultima_publicacion_dict = {}
            amonestaciones = {}
            baneos_temporales = {}
            permisos_inactividad = {}
            ticket_counter = 0
            active_conversations = {}
            faq_data = {}
            faltas_dict = {}
            mensajes_recientes = {}
    except Exception as e:
        print(f"Error al cargar el estado: {e}")
    finally:
        session.close()

def save_state(log=False):
    global last_save_time
    current_time = time.time()
    if current_time - last_save_time < SAVE_STATE_DELAY:
        return
    session = Session()
    try:
        state = session.query(State).first() or State(id="global")
        state.ultima_publicacion_dict = {str(k): v.isoformat() for k, v in ultima_publicacion_dict.items()}
        state.amonestaciones = {str(k): [t.isoformat() for t in v] for k, v in amonestaciones.items()}
        state.baneos_temporales = {str(k): v.isoformat() if v else None for k, v in baneos_temporales.items()}
        state.permisos_inactividad = {str(k): {"inicio": v["inicio"].isoformat(), "duracion": v["duracion"]} if v else None for k, v in permisos_inactividad.items()}
        state.ticket_counter = ticket_counter
        state.active_conversations = active_conversations
        state.faq_data = faq_data
        state.faltas_dict = {
            str(k): {
                "faltas": v["faltas"],
                "aciertos": v["aciertos"],
                "estado": v["estado"],
                "mensaje_id": v["mensaje_id"],
                "ultima_falta_time": v["ultima_falta_time"].isoformat() if v["ultima_falta_time"] else None
            } for k, v in faltas_dict.items()
        }
        state.mensajes_recientes = {str(k): v for k, v in mensajes_recientes.items()}
        session.commit()
        last_save_time = current_time
        if log:
            asyncio.create_task(registrar_log("Estado guardado correctamente en la base de datos", categoria="estado"))
    except Exception as e:
        print(f"Error al guardar el estado: {e}")
    finally:
        session.close()
