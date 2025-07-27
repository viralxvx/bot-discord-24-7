# utils/pdf_parser.py

import asyncio
import re

REGEX_TELEFONO = r"\+?\d[\d\s\-]{7,}\d"
REGEX_EMAIL = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
REGEX_FECHA = r"\d{1,2}/\d{1,2}/\d{2,4}"


async def extraer_contactos_desde_pdf(ruta_pdf, user_id, progreso_callback=None):
    """
    Extrae contactos desde un PDF (simulado). Soporta barra de progreso.
    """
    contactos = []
    total_paginas = 10  # Simulación: reemplaza con len(pages) reales si usas PyMuPDF o PDFplumber

    for pagina_actual in range(1, total_paginas + 1):
        await asyncio.sleep(0.1)  # Simula el tiempo de análisis por página

        contacto = {
            "nombre": f"Nombre{pagina_actual}",
            "apellido": f"Apellido{pagina_actual}",
            "email": f"contacto{pagina_actual}@mail.com",
            "telefono": f"+1-809-555-{pagina_actual:04d}"
        }
        contactos.append(contacto)

        if progreso_callback:
            porcentaje = int((pagina_actual / total_paginas) * 100)
            await progreso_callback(porcentaje)

    return contactos


def analizar_linea(linea):
    resultado = {}
    if re.search(REGEX_TELEFONO, linea):
        resultado["telefono"] = re.search(REGEX_TELEFONO, linea).group().replace(" ", "")
    if re.search(REGEX_EMAIL, linea):
        resultado["email"] = re.search(REGEX_EMAIL, linea).group()
    if re.search(REGEX_FECHA, linea):
        resultado["fecha"] = re.search(REGEX_FECHA, linea).group()
    palabras = linea.strip().split()
    if len(palabras) >= 2 and all(p[0].isupper() for p in palabras[:2]):
        resultado["nombre"] = " ".join(palabras[:4])
    return resultado if resultado else None


# Pruebas locales
if name == "__main__":
    import asyncio

    async def run():
        data = await extraer_contactos_desde_pdf("/mnt/data/Test.pdf", user_id="preview")
        for d in data:
            print(d)

    asyncio.run(run())
