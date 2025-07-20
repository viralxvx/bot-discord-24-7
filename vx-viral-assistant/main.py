from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
import openai
import os
from contextlib import asynccontextmanager

# === Configuración de logs ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Configuración de OpenAI ===
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Definir evento de ciclo de vida (startup) ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Microservicio vx-viral-assistant iniciado correctamente.")
    yield

# === Crear app con sistema lifespan actualizado ===
app = FastAPI(lifespan=lifespan)

# === CORS para permitir peticiones desde el bot de Discord ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Modelo de entrada para la solicitud ===
class IdeaRequest(BaseModel):
    prompt: str
    autor: str

# === Ruta principal para recibir el comando de Discord ===
@app.post("/idea_viral")
async def generar_idea(request: IdeaRequest):
    prompt_usuario = request.prompt.strip()
    autor = request.autor.strip()

    try:
        logger.info(f"✉️ Solicitud recibida de: {autor}")
        logger.info(f"📌 Prompt: {prompt_usuario}")

        respuesta = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "Eres un experto creando contenido viral en Twitter (𝕏). "
                    "Tu trabajo es transformar cualquier idea en una publicación con alto potencial de viralidad. "
                    "Tu estilo es claro, provocador y visualmente atractivo. Siempre piensas como un algoritmo."
                )},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.7,
            max_tokens=500
        )

        contenido = respuesta.choices[0].message.content.strip()
        logger.info("✅ Respuesta generada correctamente.")
        return {"respuesta": contenido}

    except Exception as e:
        logger.error(f"❌ Error generando la respuesta: {e}")
        return {"error": "Hubo un problema generando la idea. Notifica al administrador."}
