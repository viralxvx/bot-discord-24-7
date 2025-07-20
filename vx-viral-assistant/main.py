import logging
from fastapi import FastAPI, Request
from pydantic import BaseModel
import openai
import os

# Configuración inicial
logging.basicConfig(level=logging.INFO)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Log de inicio
logging.info("✅ Microservicio vx-viral-assistant iniciado correctamente y listo para recibir comandos.")

# Estructura esperada de entrada
class IdeaRequest(BaseModel):
    prompt: str
    user_id: int
    username: str

@app.post("/generar-idea")
async def generar_idea(req: IdeaRequest):
    try:
        logging.info(f"✅ Solicitud recibida de /idea_viral por @{req.username} (ID: {req.user_id})")
        logging.info(f"🧠 Prompt enviado a GPT: {req.prompt}")

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
        logging.info(f"📩 Respuesta generada: {resultado}")
        return {"resultado": resultado}

    except Exception as e:
        logging.error(f"❌ Error procesando la solicitud de @{req.username} (ID: {req.user_id}): {e}")
        return {"error": "❌ Error generando la idea. Notifica al administrador."}
