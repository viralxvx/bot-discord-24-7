# utils/progreso.py

def crear_barra_progreso(porcentaje: int) -> str:
    """
    Genera una barra de progreso visual en texto.

    Ejemplo:
    50% [█████░░░░░]
    """
    bloques = "█" * (porcentaje // 10)
    espacios = "░" * (10 - porcentaje // 10)
    return f"{porcentaje}% [{bloques}{espacios}]"


def actualizar_progreso(etapa: str, porcentaje: int) -> str:
    """
    Devuelve un texto profesional con barra de progreso y etapa.

    Ejemplo:
    📤 Subiendo archivo...
    30% [███░░░░░░░]
    """
    barra = crear_barra_progreso(porcentaje)
    return f"**{etapa}**\n{barra}"


def progreso_final(url_csv: str, nombre_archivo: str) -> str:
    """
    Mensaje final con enlace de descarga.
    """
    return f"""✅ **Conversión completa**

**Archivo:** `{nombre_archivo}`
🔗 **Descarga tu CSV aquí:** {url_csv}

Gracias por usar **VX** – Plataforma profesional de extracción y validación de datos.
"""
