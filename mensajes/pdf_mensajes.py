# mensajes/pdf_mensajes.py

def get_panel_bienvenida_pdf():
    return """
📌 **Bienvenido al Servicio Profesional de Conversión PDF → CSV**

Este bot extrae automáticamente contactos desde documentos PDF y los convierte a CSV de forma 100% automática y visual.

---

📂 **Comandos disponibles:**

`/procesar_pdf`  
🔁 Sube un archivo PDF (máx 10MB). El bot lo analiza, extrae nombres, apellidos, correos y teléfonos (si existen) y entrega un CSV. Todo el proceso incluye barra de progreso profesional, sin duplicación de mensajes.

`/procesar_pdf_url`  
🔗 Sube un PDF desde un enlace. Ideal para archivos grandes. Se visualiza todo el proceso hasta entregar el CSV vía gofile.io.

`/exportar_csv`  
📤 Exporta el CSV final, incluso si el archivo original era muy grande. Si ya procesaste un PDF y solo necesitas el CSV, este comando lo genera y lo sube automáticamente.

`/validar_telefonos_csv`  
📱 Revisa un archivo CSV y corrige automáticamente los números telefónicos, agregando códigos de área según el país. Usa el parámetro opcional `pais="RD"` si el archivo no incluye país.

---

⚠️ **Importante:**
- Solo funciona con PDF que contengan texto legible. Archivos escaneados como imagen **no serán procesados**.
- El sistema elimina duplicados y valida formatos automáticamente.
- El canal se limpia automáticamente una hora después de completado el proceso para mantenerlo limpio.

---

🧠 Este sistema fue diseñado para miles de usuarios. Si ves esto, estás usando tecnología robusta, profesional y a prueba de fallos. Gracias por utilizar **VXbot**.
"""
