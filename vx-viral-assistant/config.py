# config.py

import os

def get_env(name, required=True):
    value = os.getenv(name)
    if required and not value:
        raise Exception(f"❌ FALTA VARIABLE DE ENTORNO: {name}")
    return value

DISCORD_TOKEN = get_env("DISCORD_TOKEN")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
GUILD_ID = int(get_env("GUILD_ID"))
CANAL_COMANDOS_ID = int(get_env("CANAL_COMANDOS_ID"))
CANAL_GPT_ID = int(get_env("CANAL_GPT_ID"))
ADMIN_ID = int(get_env("ADMIN_ID"))
