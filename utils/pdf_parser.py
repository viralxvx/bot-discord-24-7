# utils/pdf_parser.py (fragmento: función guardar_foto segura con to_thread)
import asyncio
...

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
