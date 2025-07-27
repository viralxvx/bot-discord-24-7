# mensajes/pdf_mensajes.py

def mensaje_anclado_pdf():
    return (
        """
📥 **IMPORTADOR VX DE CONTACTOS MASIVOS (PDF)**

Bienvenido al sistema inteligente de importación de contactos para campañas VX.

Puedes cargar aquí archivos PDF grandes (hasta 10,000 páginas o más), y el bot:

1. 📎 Extraerá automáticamente todos los datos:
   - Nombre completo
   - Teléfono
   - Fechas (registro y auditoría)
   - Foto (si está embebida)

2. 🧠 Guardará todo en la base de datos VX

3. 📤 Te permitirá exportar un archivo `.CSV` profesional para:
   - Campañas en X (Twitter Ads)
   - Meta (Facebook/Instagram)
   - WhatsApp masivo
   - Mailrelay / Substack
   - CRM

---

### 🛠️ CÓMO USAR

**1. Carga tu PDF aquí**
> Usa el comando:  
`/procesar_pdf`  
y adjunta el archivo PDF.

**2. Espera confirmación**
> El bot te dirá cuántos contactos fueron detectados.

**3. Exporta el resultado**
> Usa:  
`/exportar_csv nombre_pdf: nombre_del_archivo.pdf`  
Y recibirás tu archivo `.csv` descargable.

---

### 🔒 REGLAS

- Solo los administradores pueden usar este canal.
- El archivo CSV se genera por 1 hora y luego se borra automáticamente.
- Las fotos (si existen) se vinculan a cada contacto.
- Si no hay foto, el sistema igual lo procesa sin errores.
        """
    )
