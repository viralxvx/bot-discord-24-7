import os
import requests

MAILRELAY_API_KEY = os.getenv("MAILRELAY_API_KEY")
MAILRELAY_URL = "https://innovaguard.ipzmarketing.com/api/v1/subscribers"
GRUPO_ID = 2  # <-- ID real de tu grupo "Viral X - Telegram Bot"

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
    print(f"\n[MAILRELAY] Intentando crear suscriptor: {email} en grupo {GRUPO_ID}")
    try:
        r = requests.post(MAILRELAY_URL, json=data, headers=headers, timeout=10)
        print(f"[MAILRELAY] POST status: {r.status_code}, response: {r.text}")
        if r.status_code in [200, 201]:
            print(f"[MAILRELAY] Suscripción exitosa: {email} (nuevo)")
            return True, "OK"
        else:
            try:
                json_resp = r.json()
            except Exception:
                json_resp = {}
            # Si ya existe
            if "email" in json_resp.get("errors", {}):
                errors = json_resp["errors"]["email"]
                for err in errors:
                    if "Subscriber already exists" in err:
                        print(f"[MAILRELAY] El suscriptor ya existe. Intentando añadir a grupo {GRUPO_ID}...")
                        # Busca el ID del suscriptor
                        subscriber_id = buscar_id_suscriptor(email, headers)
                        if not subscriber_id:
                            print(f"[MAILRELAY] No se pudo encontrar el ID del suscriptor.")
                            return False, "YA_EXISTE"
                        # Consulta grupos actuales
                        grupos_actuales = obtener_grupos_suscriptor(subscriber_id, headers)
                        print(f"[MAILRELAY] Grupos actuales del suscriptor: {grupos_actuales}")
                        if GRUPO_ID in grupos_actuales:
                            print(f"[MAILRELAY] El suscriptor ya está en el grupo {GRUPO_ID}.")
                            return False, "YA_EXISTE"
                        # Añade grupo 2 a los grupos existentes
                        nuevos_grupos = list(set(grupos_actuales + [GRUPO_ID]))
                        actualizado = actualizar_grupos_suscriptor(subscriber_id, nuevos_grupos, headers)
                        print(f"[MAILRELAY] PATCH (añadir grupo): status: {actualizado}")
                        if actualizado:
                            print(f"[MAILRELAY] Suscriptor {email} añadido al grupo {GRUPO_ID}.")
                            return True, "OK"
                        else:
                            print(f"[MAILRELAY] No se pudo actualizar grupos de {email}.")
                            return False, "NO_UPDATE"
            msg = json_resp.get("message", "Error desconocido en Mailrelay.")
            print(f"[MAILRELAY] Otro error: {msg}")
            return False, msg
    except Exception as e:
        print(f"[MAILRELAY] Excepción: {e}")
        return False, str(e)

def buscar_id_suscriptor(email, headers):
    try:
        url = MAILRELAY_URL + f"?email={email}"
        r = requests.get(url, headers=headers, timeout=10)
        print(f"[MAILRELAY] GET suscriptor ({email}) status: {r.status_code}, response: {r.text}")
        if r.status_code == 200:
            datos = r.json()
            # Si devuelve una lista (array)
            if isinstance(datos, list) and len(datos) > 0:
                for suscriptor in datos:
                    if suscriptor.get("email", "").lower() == email.lower():
                        return suscriptor["id"]
            # Si devuelve un dict con "subscribers"
            elif isinstance(datos, dict) and "subscribers" in datos and datos["subscribers"]:
                for suscriptor in datos["subscribers"]:
                    if suscriptor.get("email", "").lower() == email.lower():
                        return suscriptor["id"]
    except Exception as e:
        print(f"[MAILRELAY] No se pudo obtener ID para {email}: {e}")
    return None

def obtener_grupos_suscriptor(subscriber_id, headers):
    try:
        url = MAILRELAY_URL + f"/{subscriber_id}"
        r = requests.get(url, headers=headers, timeout=10)
        print(f"[MAILRELAY] GET grupos ({subscriber_id}) status: {r.status_code}, response: {r.text}")
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
        print(f"[MAILRELAY] PATCH grupos ({subscriber_id}) status: {r.status_code}, response: {r.text}")
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"[MAILRELAY] No se pudo actualizar grupos de {subscriber_id}: {e}")
        return False
