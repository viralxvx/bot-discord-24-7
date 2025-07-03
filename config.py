import os

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"❌ Error: la variable de entorno '{var_name}' no está definida.")
    return int(value) if var_name != "REDIS_URL" else value

# IDs de canales
CANAL_GUIAS_ID = get_env_variable("CANAL_GUIAS")
CANAL_COMANDOS_ID = get_env_variable("CANAL_COMANDOS")
CANAL_PRESENTATE_ID = get_env_variable("CANAL_PRESENTATE")
CANAL_NORMAS_ID = get_env_variable("CANAL_NORMAS")
CANAL_FALTAS_ID = get_env_variable("CANAL_FALTAS")
CANAL_LOGS_ID = get_env_variable("CANAL_LOGS")
CANAL_OBJETIVO_ID = get_env_variable("CANAL_OBJETIVO")
CANAL_REPORTE_ID = get_env_variable("CANAL_REPORTE")
CANAL_VICTORIAS_ID = get_env_variable("CANAL_VICTORIAS")

# Otros valores
ADMIN_ID = get_env_variable("ADMIN_ID")
REDIS_URL = os.getenv("REDIS_URL")  # Redirige sin convertir a int
