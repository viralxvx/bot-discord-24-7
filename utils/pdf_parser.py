# utils/pdf_parser.py
import asyncio
import re
import os
import json
import fitz
from utils.redis_conn import redis_conn

REGEX_TELEFONO = r"(\+?\d[\d\s\-]{7,}\d)"
REGEX_EMAIL = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
REGEX_FECHA = r"\d{1,2}/\d{1,2}/\d{2,4}"

def analizar_bloque(texto):
    """Extrae teléfono y email desde un bloque de texto"""
    telefono = re.search(REGEX_TELEFONO, texto)
    email = re.search(REGEX_EMAIL, texto)

    if telefono or email:
        return {
            "telefono": telefono.group().replace(" ", "") if telefono else "",
            "email": email.group() if email else "",
            "nombre": "",  # No se puede deducir en este tipo de PDF
            "apellido": ""  # idem
        }
    return None

async def extraer_contactos_desde_pdf(ruta_pdf, user_id, progreso_callback=None):
    contactos = []
    try:
        doc = fitz.open(ruta_pdf)
    except Exception as e:
        raise Exception(f"No se pudo abrir el PDF: {e}")

    total_paginas = len(doc)

    for pagina_actual in range(1, total_paginas + 1):
        try:
            pagina = doc[pagina_actual - 1]
            texto = pagina.get_text()
            bloques = re.split(r"\n{2,}", texto)

            for bloque in bloques:
                contacto = analizar_bloque(bloque)
                if contacto:
                    contactos.append(contacto)
        except Exception as e:
            continue

        if progreso_callback:
            porcentaje = int((pagina_actual / total_paginas) * 100)
            faltan_estimado = max(1, total_paginas - pagina_actual)
            await progreso_callback(pagina_actual, total_paginas, porcentaje, faltan_estimado)

        await asyncio.sleep(0.05)  # Simula tiempo

    # Eliminar duplicados por teléfono o email
    vistos = set()
    unicos = []
    for c in contactos:
        clave = c["telefono"] + c["email"]
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(c)

    # Guardar en Redis
    nombre_archivo = os.path.basename(ruta_pdf)
    clave_redis = f"pdf:{user_id}:{nombre_archivo}:contactos"
    redis_conn.set(clave_redis, json.dumps(unicos))

    return unicos

async def extraer_datos_genericos_desde_pdf(ruta_pdf, clave_usuario):
    genericos = []
    try:
        doc = fitz.open(ruta_pdf)
    except:
        return []

    for pagina in doc:
        texto = pagina.get_text()
        lineas = texto.splitlines()
        for linea in lineas:
            if re.search(REGEX_TELEFONO, linea) or re.search(REGEX_EMAIL, linea):
                genericos.append({
                    "nombre": "",
                    "email": re.search(REGEX_EMAIL, linea).group() if re.search(REGEX_EMAIL, linea) else "",
                    "telefono": re.search(REGEX_TELEFONO, linea).group() if re.search(REGEX_TELEFONO, linea) else ""
                })

    nombre_archivo = os.path.basename(ruta_pdf)
    clave_redis = f"pdf:{clave_usuario}:{nombre_archivo}:genericos"
    redis_conn.set(clave_redis, json.dumps(genericos))
    return genericos
