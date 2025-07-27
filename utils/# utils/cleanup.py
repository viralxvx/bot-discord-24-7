# utils/cleanup.py
import os
import time

def limpiar_archivos_temporales(ruta_directorio: str, max_tiempo_segundos: int = 3600):
    ahora = time.time()
    for archivo in os.listdir(ruta_directorio):
        ruta_completa = os.path.join(ruta_directorio, archivo)
        if os.path.isfile(ruta_completa):
            tiempo_mod = os.path.getmtime(ruta_completa)
            if ahora - tiempo_mod > max_tiempo_segundos:
                os.remove(ruta_completa)
