# state_management.py
import os
import json
import datetime
from collections import defaultdict
from config import STATE_FILE  # Importa la constante original

# Usar /data para persistencia en Railway
PERSISTENT_STATE_PATH = "/data/state.json"

# ... (resto del código)

def load_state():
    # Intenta cargar desde la ruta persistente primero
    if os.path.exists(PERSISTENT_STATE_PATH):
        state_file = PERSISTENT_STATE_PATH
    else:
        state_file = STATE_FILE
    
    try:
        with open(state_file, "r") as f:
            # ... (resto del código)

def save_state():
    # Guarda siempre en la ruta persistente
    state_file = PERSISTENT_STATE_PATH
    
    # ... (resto del código)
    with open(state_file, "w") as f:
        json.dump(state, f)
