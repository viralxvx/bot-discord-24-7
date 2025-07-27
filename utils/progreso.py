# utils/progreso.py

def generar_barra_progreso(porcentaje: int, largo=20) -> str:
    bloques_llenos = int(porcentaje / 100 * largo)
    barra = "█" * bloques_llenos + "░" * (largo - bloques_llenos)
    return f"{barra} {porcentaje}%"
