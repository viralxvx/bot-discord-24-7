# utils/pdf_parser.py
import fitz  # PyMuPDF
import re
import os
import time
from datetime import datetime
from utils.redis_conn import redis_conn
import json

# =========================
# CONFIGURACIÓN
# =========================
MAX_CONTACTOS_POR_PÁGINA = 50
REGEX_TELEFONO = re.compile(r'(\+1|809|829|849|1829)[0-9\-\+ ]{7,}')

# =========================
# FUNCIÓN PRINCIPAL
# =========================
def extraer_contactos_desde_pdf(ruta_pdf: str, guardar_imagenes: bool = True, carpeta_salida: str = "data/contactos", registrar_progreso=None):
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
                        imagen_path = guardar_foto(pagina, carpeta_salida, contacto['nombre'])
                        if imagen_path:
                            contacto['foto'] = imagen_path
                    contactos.append(contacto)
                    buffer = []
            else:
                buffer.append(linea.strip())

        # Mostrar progreso cada 100 páginas
        if registrar_progreso and (idx + 1) % 100 == 0:
            transcurrido = time.time() - inicio
            progreso = int((idx + 1) / total_paginas * 100)
            estimado_total = transcurrido / ((idx + 1) / total_paginas)
            restante = estimado_total - transcurrido
            registrar_progreso(
                paginas=idx + 1,
                total=total_paginas,
                progreso=progreso,
                faltan=int(restante)
            )

    # Guardar en Redis
    clave = f"pdf:{os.path.basename(ruta_pdf)}:contactos"
    redis_conn.set(clave, json.dumps(contactos))
    redis_conn.expire(clave, 3600)

    return contactos

# =========================
# PARSEADOR DE CONTACTOS
# =========================
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

# =========================
# GUARDAR FOTOS
# =========================
def guardar_foto(pagina, carpeta, nombre_contacto):
    imagenes = pagina.get_images(full=True)
    if not imagenes:
        return None

    try:
        xref = imagenes[0][0]
        pix = fitz.Pixmap(pagina.parent, xref)
        nombre_archivo = f"{nombre_contacto.replace(' ', '_')}.jpg"
        ruta = os.path.join(carpeta, nombre_archivo)
        pix.save(ruta)
        return ruta
    except Exception as e:
        print(f"[ERROR] No se pudo guardar imagen para {nombre_contacto}: {e}")
        return None

# =========================
# TEST LOCAL
# =========================
if __name__ == "__main__":
    def test_log(**kwargs):
        print("[PROGRESO]", kwargs)

    contactos = extraer_contactos_desde_pdf("/mnt/data/Test.pdf", registrar_progreso=test_log)
    for c in contactos:
        print(c)
    print(f"Total: {len(contactos)} contactos procesados.")
