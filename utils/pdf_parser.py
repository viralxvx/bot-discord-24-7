# utils/pdf_parser.py
import fitz  # PyMuPDF
import re
import os
import time
import unicodedata
import hashlib
import inspect
from datetime import datetime
from utils.redis_conn import redis_conn
import json

MAX_CONTACTOS_POR_PÁGINA = 50
REGEX_TELEFONO = re.compile(r'(\+1|809|829|849|1829)[0-9\-\+ ]{7,}')
REGEX_UBICACION = re.compile(r'Provincia:\s*(.*?)\s*\|\s*Circ:\s*(\d+)\s*\|\s*Municipio:\s*(.*?)\s*(\||$)')

async def extraer_contactos_desde_pdf(ruta_pdf: str, guardar_imagenes: bool = True, carpeta_salida: str = "data/contactos", registrar_progreso=None):
    inicio = time.time()
    doc = fitz.open(ruta_pdf)
    total_paginas = len(doc)
    contactos = []

    if guardar_imagenes and not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    for idx, pagina in enumerate(doc):
        texto = pagina.get_text()
        lineas = texto.splitlines()

        ubicacion = {
            "provincia": None,
            "municipio": None,
            "circunscripcion": None
        }
        for linea in lineas:
            match = REGEX_UBICACION.search(linea)
            if match:
                ubicacion["provincia"] = match.group(1).strip()
                ubicacion["circunscripcion"] = match.group(2).strip()
                ubicacion["municipio"] = match.group(3).strip()
                break

        buffer = []
        for linea in lineas:
            if re.search(REGEX_TELEFONO, linea):
                buffer.append(linea.strip())
                contacto = parsear_contacto(buffer)
                if contacto:
                    contacto.update(ubicacion)
                    if guardar_imagenes:
                        imagen_path = guardar_foto(pagina, carpeta_salida, contacto['nombre'])
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

    clave = f"pdf:{os.path.basename(ruta_pdf)}:contactos"
    redis_conn.set(clave, json.dumps(contactos))
    redis_conn.expire(clave, 3600)

    return contactos


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


def guardar_foto(pagina, carpeta, nombre_contacto):
    imagenes = pagina.get_images(full=True)
    if not imagenes:
        return None

    try:
        xref = imagenes[0][0]
        pix = fitz.Pixmap(pagina.parent, xref)
        nombre_archivo_limpio = limpiar_nombre_archivo(nombre_contacto)
        hash_n = hashlib.md5(nombre_contacto.encode()).hexdigest()[:6]
        nombre_archivo = f"{nombre_archivo_limpio}_{hash_n}.jpg"
        ruta = os.path.join(carpeta, nombre_archivo)
        pix.save(ruta)
        return ruta
    except Exception as e:
        print(f"[ERROR] No se pudo guardar imagen para {nombre_contacto}: {e}")
        return None


if __name__ == "__main__":
    import asyncio

    async def test_log(**kwargs):
        print("[PROGRESO]", kwargs)

    async def run():
        contactos = await extraer_contactos_desde_pdf("/mnt/data/Test.pdf", registrar_progreso=test_log)
        for c in contactos:
            print(c)
        print(f"Total: {len(contactos)} contactos procesados.")

    asyncio.run(run())
