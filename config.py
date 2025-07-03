import os

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"❌ Error: la variable de entorno '{var_name}' no está definida.")
    return int(value)

CANAL_GUIAS_ID = get_env_variable("CANAL_GUIAS")       # 📖guías
CANAL_COMANDOS_ID = get_env_variable("CANAL_COMANDOS") # 💻comandos
CANAL_PRESENTATE_ID = get_env_variable("CANAL_PRESENTATE")
CANAL_NORMAS_ID = get_env_variable("CANAL_NORMAS")
CANAL_FALTAS_ID = get_env_variable("CANAL_FALTAS")
CANAL_LOGS_ID = get_env_variable("CANAL_LOGS")
CANAL_OBJETIVO_ID = get_env_variable("CANAL_OBJETIVO")
CANAL_REPORTE_ID = get_env_variable("CANAL_REPORTE")
ADMIN_ID = get_env_variable("ADMIN_ID")
