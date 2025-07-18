import os
import requests

MAILRELAY_API_KEY = os.getenv("MAILRELAY_API_KEY")
MAILRELAY_URL = "https://innovaguard.ipzmarketing.com/api/v1/subscribers"  # Tu subdominio correcto
GRUPO_ID = 2

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
        "groups": [GRUPO_ID]
    }
    # Intentar crear el suscriptor
    try:
        r = requests.post(MAILRELAY_URL, json=data, headers=headers, timeout=10)
        if r.status_code in [200, 201]:
            print(f"[MAILRELAY] Suscripción exitosa: {email} (nuevo)")
            return True, "OK"
        else:
            print(f"[MAILRELAY] Error ({r.status_code}): {r.text}")
            try:
                json_resp = r.json()
                # ¿Ya existe?
                if "email" in json_resp.get("errors", {}):
                    errors = json_resp["errors"]["email"]
                    for err in errors:
                        if "Subscriber already exists" in err:
                            # Buscar ID de ese suscriptor
                            subscriber_id = buscar_id_suscriptor(email, headers)
                            if not subscriber_id:
                                return False, "YA_EXISTE"
                            # Consultar los grupos actuales
                            grupos_actuales = obtener_grupos_suscriptor(subscriber_id, headers)
                            if GRUPO_ID in grupos_actuales:
                                # Ya está en el grupo correcto
                                print(f"[MAILRELAY] Ya estaba en el grupo {GRUPO_ID}: {email}")
                                return False, "YA_EXISTE"
                            # Añadir grupo 2 a los grupos existentes
                            nuevos_grupos = list(set(grupos_actuales + [GRUPO_ID]))
                            # Actualizar suscriptor
                            actualizado = actualizar_grupos_suscriptor(subscriber_id, nuevos_grupos, headers)
                            if actualizado:
                                print(f"[MAILRELAY] Suscriptor {email} añadido a grupo {GRUPO_ID}.")
                                return True, "OK"
                            else:
                                print(f"[MAILRELAY] No se pudo actualizar grupos de {email}.")
                                return False, "NO_UPDATE"
                msg = json_resp.get("message", "Error desconocido en Mailrelay.")
            except Exception as e:
                msg = f"Error desconocido en Mailrelay. Exception: {e}"
            return False, msg
    except Exception as e:
        print(f"[MAILRELAY] Excepción: {e}")
        return False, str(e)

def buscar_id_suscriptor(email, headers):
    try:
        url = MAILRELAY_URL + f"?email={email}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            datos = r.json()
            if datos and "subscribers" in datos and datos["subscribers"]:
                return datos["subscribers"][0]["id"]
    except Exception as e:
        print(f"[MAILRELAY] No se pudo obtener ID para {email}: {e}")
    return None

def obtener_grupos_suscriptor(subscriber_id, headers):
    try:
        url = MAILRELAY_URL + f"/{subscriber_id}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            datos = r.json()
            return datos.get("groups", [])
    except Exception as e:
        print(f"[MAILRELAY] No se pudo obtener grupos de {subscriber_id}: {e}")
    return []

def actualizar_grupos_suscriptor(subscriber_id, grupos, headers):
    try:
        url = MAILRELAY_URL + f"/{subscriber_id}"
        data = {"groups": grupos}
        r = requests.patch(url, json=data, headers=headers, timeout=10)
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"[MAILRELAY] No se pudo actualizar grupos de {subscriber_id}: {e}")
        return False
