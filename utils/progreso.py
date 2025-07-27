# utils/progreso.py

def generar_barra_progreso(porcentaje: int) -> str:
    bloques_totales = 20
    bloques_llenos = int((porcentaje / 100) * bloques_totales)
    bloques_vacios = bloques_totales - bloques_llenos

    barra = "█" * bloques_llenos + "░" * bloques_vacios
    return f"[{barra}] {porcentaje}%"
