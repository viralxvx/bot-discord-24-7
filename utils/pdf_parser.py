# utils/pdf_parser.py
import asyncio
import re
import os
import json
from utils.redis_conn import redis_conn

REGEX_TELEFONO = r"\+?\d[\d\s\-]{7,}\d"
REGEX_EMAIL = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
REGEX_NOMBRE_COMPLETO = r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+$"

async def extraer_contactos_desde_pdf(rutas_paginas, pdf_id, user_id=None, registrar_progreso=None):
    contactos = []
    textos = []

    for ruta in rutas_paginas:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
            textos.append(contenido)

    texto_total = "\n".join(textos)
    bloques = re.split(r"\n\s*\n", texto_total)

    for bloque in bloques:
        lineas = bloque.strip().splitlines()
        nombre, apellido, email, telefono = None, None, None, None

        for linea in lineas:
            linea = linea.strip()

            if not email:
                match_email = re.search(REGEX_EMAIL, linea)
                if match_email:
                    email = match_email.group()

            if not telefono:
                match_telefono = re.search(REGEX_TELEFONO, linea)
                if match_telefono:
                    telefono = re.sub(r"[^\d+]", "", match_telefono.group())

            if not nombre or not apellido:
                partes = linea.split()
                if len(partes) >= 2 and all(p[0].isupper() for p in partes[:2]):
                    posible_nombre = partes[0]
                    posible_apellido = partes[1]
                    if not nombre:
                        nombre = posible_nombre
                    if not apellido:
                        apellido = posible_apellido

        if email or telefono:
            contactos.append({
                "nombre": nombre or "",
                "apellido": apellido or "",
                "email": email or "",
                "telefono": telefono or ""
            })

    contactos_unicos = []
    vistos = set()
    for contacto in contactos:
        clave = (contacto["email"], contacto["telefono"])
        if clave not in vistos:
            vistos.add(clave)
            contactos_unicos.append(contacto)

    redis_conn.set(f"pdf_contactos:{pdf_id}", json.dumps(contactos_unicos), ex=3600)
    return contactos_unicos

# 🔧 Restaurado por compatibilidad con comandos.procesar_pdf
async def extraer_datos_genericos_desde_pdf(rutas_paginas, pdf_id, user_id=None, registrar_progreso=None):
    return await extraer_contactos_desde_pdf(rutas_paginas, pdf_id, user_id, registrar_progreso)
