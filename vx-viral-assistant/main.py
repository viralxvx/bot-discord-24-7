# main.py
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import uvicorn

# ========== LOGGING PATCH (para evitar errores de formato) ==========
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

# ========== FASTAPI INIT ==========
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== CLIENTE OPENAI ==========
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== ENDPOINT: /idea_viral ==========
@app.post("/idea_viral")
async def idea_viral(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    autor = data.get("autor", "")
    logger.info(f"🔹 Solicitud recibida de {autor} con prompt: {prompt}")

    return {
        "respuesta": f"🎯 Hola {autor}, una idea viral sobre '{prompt}' sería: Comparte un antes y después impactante acompañado de una lección poderosa. Usa contraste visual + emoción."
    }

# ========== ENDPOINT: /hablar (ChatGPT libre) ==========
@app.post("/hablar")
async def hablar(request: Request):
    try:
        data = await request.json()
        mensaje = data.get("mensaje", "")
        autor = data.get("autor", "")

        logging.info(f"🧠 Solicitud de conversación recibida de {autor}: {mensaje}")

        respuesta = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente conversacional inteligente en Discord"},
                {"role": "user", "content": mensaje}
            ],
            temperature=0.8
        )

        texto = respuesta.choices[0].message.content.strip()
        return {"respuesta": texto}

    except Exception as e:
        logging.error(f"❌ Error en /hablar: {e}")
        return {"respuesta": "⚠️ Error procesando tu mensaje. Contacta al administrador."}

# ========== ENDPOINT: /health ==========
@app.get("/health")
async def health_check():
    return {"status": "ok", "mensaje": "Servicio activo"}

# ========== INICIO UVICORN ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
