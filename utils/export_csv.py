# utils/export_csv.py
import csv
import os
import tempfile
import json
from utils.redis_conn import redis_conn

# =============================
# EXPORTADOR A CSV DESDE REDIS
# =============================
def exportar_contactos_csv(nombre_archivo_pdf: str) -> str:
    clave_redis = f"pdf:{nombre_archivo_pdf}:contactos"
    datos_json = redis_conn.get(clave_redis)

    if not datos_json:
        raise Exception(f"❌ No se encontró información en Redis para: {clave_redis}")

    contactos = json.loads(datos_json)

    campos = [
        "nombre", "telefono", "fecha_ingreso", "fecha_auditoria", "provincia", "municipio", "circunscripcion", "foto"
    ]

    tmp_dir = tempfile.gettempdir()
    ruta_csv = os.path.join(tmp_dir, f"contactos_{nombre_archivo_pdf}.csv")

    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for contacto in contactos:
            writer.writerow({campo: contacto.get(campo, "") for campo in campos})

    return ruta_csv

# =============================
# TEST LOCAL (opcional)
# =============================
if __name__ == "__main__":
    ruta = exportar_contactos_csv("Test.pdf")
    print(f"CSV generado: {ruta}")
