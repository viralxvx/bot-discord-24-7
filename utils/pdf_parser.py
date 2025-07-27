import asyncio
import re
import os
import json
from utils.redis_conn import redis_conn

REGEX_TELEFONO = r"\+?\d[\d\s\-]{7,}\d"
REGEX_EMAIL = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
REGEX_FECHA = r"\d{1,2}/\d{1,2}/\d{2,4}"

async def extraer_contactos_desde_pdf(ruta_pdf, user_id, registrar_progreso=None):
    import fitz
    contactos = []
    doc = fitz.open(ruta_pdf)
    total_paginas = len(doc)

    for i, pagina in enumerate(doc, start=1):
        texto = pagina.get_text("text")
        lineas = texto.splitlines()
        for linea in lineas:
            datos = analizar_linea(linea)
            if datos and "email" in datos and "telefono" in datos:
                contactos.append(datos)

        if registrar_progreso:
            porcentaje = int((i / total_paginas) * 100)
            await registrar_progreso(i, total_paginas, porcentaje, 1)

    contactos_unicos = {json.dumps(c, sort_keys=True) for c in contactos}
    contactos = [json.loads(c) for c in contactos_unicos]

    nombre_archivo = os.path.basename(ruta_pdf)
    clave = f"pdf:{user_id}:{nombre_archivo}:contactos"
    redis_conn.set(clave, json.dumps(contactos), ex=3600)

    return contactos

async def extraer_datos_genericos_desde_pdf(ruta_pdf, clave_usuario):
    import fitz
    doc = fitz.open(ruta_pdf)
    registros = []
    for pagina in doc:
        texto = pagina.get_text("text")
        lineas = texto.splitlines()
        for linea in lineas:
            datos = analizar_linea(linea)
            if datos:
                registros.append(datos)
    nombre_archivo = os.path.basename(ruta_pdf)
    clave = f"pdf:{clave_usuario}:{nombre_archivo}:genericos"
    redis_conn.set(clave, json.dumps(registros), ex=3600)
    return registros

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
