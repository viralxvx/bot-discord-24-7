# main.py
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ================== LOGGING PATCH (UVICORN BUG FIX) ==================
class SafeFormatter(logging.Formatter):
    def formatMessage(self, record):
        try:
            return super().formatMessage(record)
        except ValueError:
            return f"{record.name} - {record.getMessage()}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.access")
for handler in logger.handlers:
    handler.setFormatter(SafeFormatter('%(asctime)s - %(levelname)s - %(message)s'))

# ================== FASTAPI INIT ==================
app = FastAPI()

# Middleware de CORS (opcional pero útil)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== ENDPOINT PRINCIPAL ==================
@app.post("/idea_viral")
async def idea_viral(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    autor = data.get("autor", "")

    logger.info(f"🔹 Solicitud recibida de {autor} con prompt: {prompt}")

    # Ejemplo de respuesta temporal (sin OpenAI todavía)
    return {
        "respuesta": f"🎯 Hola {autor}, una idea viral sobre '{prompt}' sería: Comparte un antes y después impactante acompañado de una lección poderosa. Usa contraste visual + emoción."
    }

# ================== TEST DE SALUD ==================
@app.get("/health")
async def health_check():
    return {"status": "ok", "mensaje": "Servicio activo"}

# ================== INICIO UVICORN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
