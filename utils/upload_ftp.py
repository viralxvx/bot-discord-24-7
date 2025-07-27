# utils/upload_ftp.py
import os
from ftplib import FTP

def subir_a_ftp(ruta_local: str, nombre_remoto: str) -> str:
    host = "ftp.innovaguard.shop"
    port = 21
    usuario = "viralx@innovaguard.shop"
    contrasena = "wQDnmiLE4QpKJC"
    carpeta_remota = "/public_html/csv"

    try:
        ftp = FTP()
        ftp.connect(host, port, timeout=10)
        ftp.login(user=usuario, passwd=contrasena)
        ftp.cwd(carpeta_remota)

        with open(ruta_local, "rb") as archivo:
            ftp.storbinary(f"STOR {nombre_remoto}", archivo)

        ftp.quit()
        url = f"https://innovaguard.shop/csv/{nombre_remoto}"
        return url

    except Exception as e:
        raise Exception(f"❌ Error al subir archivo al FTP: {e}")
