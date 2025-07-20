import logging
from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os
from datetime import datetime

# ========= CONFIGURACIÓN =========

# Clave de OpenAI desde variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurar logs: consola + archivo
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_file = "gpt_logs.log"

# Handler para archivo
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(log_formatter)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Configurar logger principal
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Iniciar app
app = FastAPI()
logger.info("✅ Microservicio vx-viral-assistant iniciado correctamente.")

# ========= ESTRUCTURA DE ENTRADA =========
class IdeaRequest(BaseModel):
    prompt: str
    user_id: int
    username: str

# ========= ENDPOINT PRINCIPAL =========
@app.post("/generar-idea")
async def generar_idea(req: IdeaRequest):
    try:
        logger.info(f"🟢 Solicitud recibida de /idea_viral por @{req.username} (ID: {req.user_id})")
        logger.info(f"🧠 Prompt: {req.prompt}")

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en ideas virales para X (Twitter). Responde solo con la idea, sin rodeos."},
                {"role": "user", "content": req.prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        resultado = response.choices[0].message.content.strip()
        logger.info(f"✅ Respuesta generada para @{req.username}: {resultado}")
        return {"resultado": resultado}

    except Exception as e:
        logger.error(f"❌ Error procesando solicitud de @{req.username}: {e}")
        return {"error": "❌ Error generando la idea. Notifica al administrador."}
