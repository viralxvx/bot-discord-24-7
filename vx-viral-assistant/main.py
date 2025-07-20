# main.py
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import openai

# ================== CONFIGURACIÓN ==================
openai.api_key = os.getenv("OPENAI_API_KEY")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== ENDPOINT: IDEA VIRAL ==================
@app.post("/idea_viral")
async def idea_viral(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    autor = data.get("autor", "")

    logger.info(f"🔹 Solicitud recibida de {autor} con prompt: {prompt}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Responde con ideas virales breves, visuales y potentes, ideales para crecer en X."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        return {"respuesta": content}

    except Exception as e:
        logger.error(f"❌ Error generando idea viral: {e}")
        return {"respuesta": "❌ Error generando la idea viral. Intenta de nuevo más tarde."}

# ================== ENDPOINT: HABLAR LIBRE ==================
@app.post("/hablar")
async def hablar(request: Request):
    data = await request.json()
    mensaje = data.get("mensaje", "")
    autor = data.get("autor", "anónimo")

    logger.info(f"🧠 Solicitud de conversación recibida de {autor}: {mensaje}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Responde como ChatGPT en una conversación informal, clara y útil."},
                {"role": "user", "content": mensaje}
            ]
        )
        contenido = response.choices[0].message.content.strip()
        return {"respuesta": contenido}
    except Exception as e:
        logger.error(f"❌ Error en /hablar: {e}")
        return {"respuesta": "❌ Ocurrió un error procesando tu mensaje."}

# ================== TEST DE SALUD ==================
@app.get("/health")
async def health_check():
    return {"status": "ok", "mensaje": "Servicio activo"}

# ================== INICIO UVICORN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
