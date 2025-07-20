import os
import sys
import asyncio
import logging
import openai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# ============ Parche de logging resiliente para Uvicorn ============
from uvicorn.logging import DefaultFormatter

class SafeFormatter(DefaultFormatter):
    def formatMessage(self, record):
        try:
            return super().formatMessage(record)
        except ValueError:
            return f"{record.name} - {record.getMessage()}"

# Configurar logs seguros
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("uvicorn.access")
for handler in logger.handlers:
    handler.setFormatter(SafeFormatter(fmt="%(asctime)s - %(levelprefix)s %(message)s"))

# ============ Configuración OpenAI ============
openai.api_key = os.getenv("OPENAI_API_KEY")

# ============ FastAPI con ciclo de vida ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("✅ Microservicio vx-viral-assistant iniciado correctamente.")
    yield

app = FastAPI(lifespan=lifespan)

# ============ Middleware ============
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📥 Solicitud recibida: {request.method} {request.url}")
    return await call_next(request)

# CORS global
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Modelos ============
class IdeaRequest(BaseModel):
    prompt: str
    autor: str

# ============ Endpoints ============
@app.post("/idea_viral")
async def idea_viral(req: IdeaRequest):
    prompt = req.prompt.strip()
    autor = req.autor.strip()

    try:
        logger.info(f"✉️ Autor: {autor}")
        logger.info(f"🧠 Prompt recibido: {prompt}")

        completion = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "Eres un experto creando contenido viral para X (Twitter). "
                    "Tu misión es transformar ideas en hilos con alto potencial de viralidad. "
                    "Tu estilo es directo, provocador y visualmente claro. Siempre piensas como un algoritmo."
                )},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        resultado = completion.choices[0].message.content.strip()
        logger.info("✅ Idea generada con éxito.")
        return {"respuesta": resultado}

    except Exception as e:
        logger.error(f"❌ Error generando idea: {e}")
        return {"error": "Hubo un problema generando la idea. Notifica al administrador."}

@app.get("/health")
async def health():
    return {"status": "ok", "servicio": "vx-viral-assistant"}

@app.post("/test_log")
async def test_log(request: Request):
    body = await request.json()
    logger.info(f"🧪 Test de logs recibido: {body}")
    return {"log": "OK"}
