# utils/pdf_parser.py

import asyncio
import re
import os
import json
import fitz
from utils.redis_conn import redis_conn

# =============================
# Expresiones regulares comunes
# =============================
REGEX_TELEFONO = r"\+?\d[\d\s\-]{7,}\d"
REGEX_EMAIL = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
REGEX_FECHA = r"\d{1,2}/\d{1,2}/\d{2,4}"

# =============================
# EXTRACCIÓN PRINCIPAL DE CONTACTOS
# =============================
async def extraer_contactos_desde_pdf(ruta_pdf, clave_usuario=None, registrar_progreso=None):
    doc = fitz.open(ruta_pdf)
    total_paginas = len(doc)
    resultados = []

    for i, pagina in enumerate(doc, start=1):
        texto = pagina.get_text()
        lineas = texto.split("\n")
        for linea in lineas:
            datos = analizar_linea(linea)
            if datos:
                resultados.append(datos)

        if registrar_progreso:
            porcentaje = int((i / total_paginas) * 100)
            faltan = max(1, total_paginas - i)
            await registrar_progreso(i, total_paginas, porcentaje, faltan)

        await asyncio.sleep(0.05)  # Simulación de carga

    if clave_usuario:
        clave_redis = f"pdf:{clave_usuario}:{os.path.basename(ruta_pdf)}:contactos"
        redis_conn.set(clave_redis, json.dumps(resultados), ex=3600)

    return resultados

# =============================
# MODO GENÉRICO DE EMERGENCIA
# =============================
async def extraer_datos_genericos_desde_pdf(ruta_pdf: str, clave_usuario: str = None) -> list:
    doc = fitz.open(ruta_pdf)
    resultados = []
    for pagina in doc:
        texto = pagina.get_text()
        lineas = texto.split("\n")
        for linea in lineas:
            datos = analizar_linea(linea)
            if datos:
                resultados.append(datos)
    if clave_usuario:
        clave_redis = f"pdf:{clave_usuario}:{os.path.basename(ruta_pdf)}:contactos_genericos"
        redis_conn.set(clave_redis, json.dumps(resultados), ex=3600)
    return resultados

# =============================
# ANÁLISIS DE CADA LÍNEA
# =============================
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

# =============================
# PRUEBA LOCAL
# =============================
if __name__ == "__main__":
    import asyncio

    async def run():
        ruta = "/mnt/data/Test.pdf"
        contactos = await extraer_contactos_desde_pdf(ruta, clave_usuario="prueba_local")
        print("Contactos:")
        for contacto in contactos:
            print(contacto)
        print("---")
        genericos = await extraer_datos_genericos_desde_pdf(ruta, clave_usuario="prueba_local")
        print("Genéricos:")
        for g in genericos:
            print(g)

    asyncio.run(run())
