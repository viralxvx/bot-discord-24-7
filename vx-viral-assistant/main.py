import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
import logging

# Configurar logging visible en Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CARGAR VARIABLES DE ENTORNO ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# === MODELO DE DATOS ===
class IdeaRequest(BaseModel):
    prompt: str
    usuario: str

# === INICIALIZAR APP FASTAPI ===
app = FastAPI()

# === PERMISOS CORS PARA PETICIONES EXTERNAS (opcional) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ENDPOINT PRINCIPAL ===
@app.post("/generar_idea")
async def generar_idea(req: IdeaRequest):
    logger.info(f"🧠 Recibida solicitud de idea para: {req.usuario}")
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en crear ideas virales para X. Responde con una idea clara y breve."},
                {"role": "user", "content": req.prompt}
            ],
            max_tokens=300
        )
        idea = respuesta.choices[0].message["content"].strip()
        logger.info("✅ Idea generada correctamente desde OpenAI")
        return {"idea": idea}
    except Exception as e:
        logger.error(f"❌ Error al generar idea con OpenAI: {e}")
        return {"error": "Error al generar la idea con OpenAI"}

# === MENSAJE INICIAL DE STATUS ===
@app.on_event("startup")
async def startup_event():
    logger.info("✅ Microservicio vx-viral-assistant iniciado correctamente.")
