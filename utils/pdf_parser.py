# utils/pdf_parser.py
import asyncio
import re
import os
import json
import fitz
from utils.redis_conn import redis_conn

REGEX_TELEFONO = r"(\+?\d{3,4}[-\s]?\d{3}[-\s]?\d{4})"
REGEX_EMAIL = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

def limpiar_linea(linea):
    return linea.strip().replace("–", "-").replace("—", "-").replace("•", "")

def extraer_contacto(lineas):
    contacto = {"telefono": "", "email": "", "nombre": "", "apellido": ""}
    for linea in lineas:
        l = limpiar_linea(linea)

        if not contacto["telefono"]:
            tel_match = re.search(REGEX_TELEFONO, l)
            if tel_match:
                contacto["telefono"] = tel_match.group().replace(" ", "").replace("-", "")

        if not contacto["email"]:
            email_match = re.search(REGEX_EMAIL, l)
            if email_match:
                contacto["email"] = email_match.group()

        palabras = l.split()
        if len(palabras) >= 2 and palabras[0][0].isupper() and palabras[1][0].isupper():
            contacto["nombre"] = palabras[0]
            contacto["apellido"] = palabras[1]

    if contacto["telefono"] or contacto["email"]:
        return contacto
    return None

async def extraer_contactos_desde_pdf(ruta_pdf, user_id, registrar_progreso=None):
    contactos = []
    doc = fitz.open(ruta_pdf)
    total_paginas = len(doc)

    for idx, pagina in enumerate(doc, start=1):
        texto = pagina.get_text()
        bloques = texto.split("\n\n")
        for bloque in bloques:
            lineas = bloque.strip().splitlines()
            c = extraer_contacto(lineas)
            if c:
                contactos.append(c)

        if registrar_progreso:
            porcentaje = int((idx / total_paginas) * 100)
            faltan = total_paginas - idx
            await registrar_progreso(idx, total_paginas, porcentaje, faltan)
        await asyncio.sleep(0.05)

    # Eliminar duplicados
    vistos = set()
    unicos = []
    for c in contactos:
        clave = (c["telefono"], c["email"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(c)

    nombre_archivo = os.path.basename(ruta_pdf)
    clave_redis = f"pdf:{user_id}:{nombre_archivo}:contactos"
    redis_conn.set(clave_redis, json.dumps(unicos))

    return unicos

async def extraer_datos_genericos_desde_pdf(ruta_pdf, clave_usuario):
    genericos = []
    doc = fitz.open(ruta_pdf)

    for pagina in doc:
        texto = pagina.get_text()
        for linea in texto.splitlines():
            l = limpiar_linea(linea)
            tel = re.search(REGEX_TELEFONO, l)
            email = re.search(REGEX_EMAIL, l)
            if tel or email:
                genericos.append({
                    "telefono": tel.group().replace("-", "") if tel else "",
                    "email": email.group() if email else "",
                    "nombre": "",
                    "apellido": ""
                })

    nombre_archivo = os.path.basename(ruta_pdf)
    clave_redis = f"pdf:{clave_usuario}:{nombre_archivo}:genericos"
    redis_conn.set(clave_redis, json.dumps(genericos))

    return genericos
