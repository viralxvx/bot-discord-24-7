# utils/mailrelay.py

import os
import requests

MAILRELAY_API_KEY = os.getenv("MAILRELAY_API_KEY")
MAILRELAY_URL = "https://innovaguard.ipzmarketing.com/api/v1/subscribers"  # Tu subdominio correcto

def suscribir_email(email):
    if not MAILRELAY_API_KEY or "innovaguard" not in MAILRELAY_URL:
        print("[MAILRELAY] Configuración incompleta.")
        return False, "Configuración de Mailrelay incompleta."

    headers = {
        "X-Auth-Token": MAILRELAY_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "status": "active",
        "groups": [2]  # <-- ID de tu grupo "Viral X - Telegram Bot"
    }
    try:
        r = requests.post(MAILRELAY_URL, json=data, headers=headers, timeout=10)
        if r.status_code in [200, 201]:
            print(f"[MAILRELAY] Suscripción exitosa: {email}")
            return True, "OK"
        else:
            print(f"[MAILRELAY] Error ({r.status_code}): {r.text}")
            # Intenta obtener mensaje de error de la respuesta
            try:
                msg = r.json().get("message", "Error desconocido en Mailrelay.")
            except Exception:
                msg = "Error desconocido en Mailrelay."
            return False, msg
    except Exception as e:
        print(f"[MAILRELAY] Excepción: {e}")
        return False, str(e)
