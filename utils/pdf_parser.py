# utils/pdf_parser.py (completo con ambas funciones: estructurada y genérica)
import fitz  # PyMuPDF
import re
import os
import time
import unicodedata
import hashlib
import inspect
import asyncio
from datetime import datetime
from utils.redis_conn import redis_conn
import json

REGEX_TELEFONO = re.compile(r'(\+1|809|829|849|1829)[0-9\-\+ ]{7,}')
REGEX_EMAIL = re.compile(r'\b[\w.-]+@[\w.-]+\.\w+\b')
REGEX_FECHA = re.compile(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})')

async def extraer_contactos_desde_pdf(ruta_pdf: str, guardar_imagenes: bool = True, carpeta_salida: str = "data/contactos", registrar_progreso=None, clave_usuario: str = None):
    inicio = time.time()
    doc = fitz.open(ruta_pdf)
    total_paginas = len(doc)
    contactos = []

    if guardar_imagenes and not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    for idx, pagina in enumerate(doc):
        texto = pagina.get_text()
        lineas = texto.splitlines()

        buffer = []
        for linea in lineas:
            if re.search(REGEX_TELEFONO, linea):
                buffer.append(linea.strip())
                contacto = parsear_contacto(buffer)
                if contacto:
                    if guardar_imagenes:
                        imagen_path = await guardar_foto(pagina, carpeta_salida, contacto['nombre'])
                        if imagen_path:
                            contacto['foto'] = imagen_path
                    contactos.append(contacto)
                    buffer = []
            else:
                buffer.append(linea.strip())

        if registrar_progreso and (idx + 1) % 100 == 0:
            transcurrido = time.time() - inicio
            progreso = int((idx + 1) / total_paginas * 100)
            estimado_total = transcurrido / ((idx + 1) / total_paginas)
            restante = estimado_total - transcurrido

            progreso_info = dict(
                paginas=idx + 1,
                total=total_paginas,
                progreso=progreso,
                faltan=int(restante)
            )

            if inspect.iscoroutinefunction(registrar_progreso):
                await registrar_progreso(**progreso_info)
            else:
                registrar_progreso(**progreso_info)

    nombre_base = os.path.basename(ruta_pdf)
    clave = f"pdf:{clave_usuario}:{nombre_base}:contactos" if clave_usuario else f"pdf:{nombre_base}:contactos"
    redis_conn.set(clave, json.dumps(contactos))
    redis_conn.expire(clave, 3600)

    return contactos


async def extraer_datos_genericos_desde_pdf(ruta_pdf: str, clave_usuario: str = None):
    doc = fitz.open(ruta_pdf)
    registros = []
    for pagina in doc:
        texto = pagina.get_text()
        lineas = texto.splitlines()

        for linea in lineas:
            if not linea.strip():
                continue

            registro = analizar_linea(linea)
            if registro:
                registros.append(registro)

    clave = f"pdf:{clave_usuario}:{os.path.basename(ruta_pdf)}:generico"
    redis_conn.set(clave, json.dumps(registros))
    redis_conn.expire(clave, 3600)

    return registros


def parsear_contacto(lineas):
    texto = " ".join(lineas)
    telefono = re.search(REGEX_TELEFONO, texto)
    if not telefono:
        return None

    partes = texto.split(telefono.group(0))
    nombre_completo = partes[0].strip()
    fechas = re.findall(r'\d{4}-\d{2}-\d{2}', texto)

    return {
        "nombre": nombre_completo,
        "telefono": telefono.group(0).replace(" ", ""),
        "fecha_ingreso": fechas[0] if len(fechas) > 0 else None,
        "fecha_auditoria": fechas[1] if len(fechas) > 1 else None,
    }


def limpiar_nombre_archivo(texto):
    texto = texto.strip().replace(" ", "_")
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zA-Z0-9_\-]', '', texto)
    return texto[:80]


async def guardar_foto(pagina, carpeta, nombre_contacto):
    imagenes = pagina.get_images(full=True)
    if not imagenes:
        return None

    try:
        xref = imagenes[0][0]
        pix = fitz.Pixmap(pagina.parent, xref)
        nombre_archivo_limpio = limpiar_nombre_archivo(nombre_contacto)
        hash_n = hashlib.md5(nombre_contacto.encode()).hexdigest()[:6]
        nombre_archivo = f"{nombre_archivo_limpio}_{hash_n}.jpg"
        ruta = os.path.join(carpeta, nombre_archivo[:120])
        await asyncio.to_thread(pix.save, ruta)
        return ruta
    except Exception as e:
        print(f"[ERROR] No se pudo guardar imagen para {nombre_contacto}: {e}")
        return None


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


if __name__ == "__main__":
    import asyncio

    async def run():
        data = await extraer_datos_genericos_desde_pdf("/mnt/data/Test.pdf", clave_usuario="preview")
        for d in data:
            print(d)
        print("---")
        data2 = await extraer_contactos_desde_pdf("/mnt/data/Test.pdf", clave_usuario="preview")
        for d in data2:
            print(d)

    asyncio.run(run())
