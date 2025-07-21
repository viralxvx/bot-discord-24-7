from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import requests

app = FastAPI()

HF_TOKEN = os.environ["HF_TOKEN"]
MODEL = "moonshotai/Kimi-K2-Instruct"  # Cambia por el que quieras

class MessageRequest(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_endpoint(req: MessageRequest):
    endpoint = "https://api.huggingface.co/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": req.prompt}
        ],
        "max_tokens": 400,
        "temperature": 0.7,
        "stream": False,
    }
    r = requests.post(endpoint, headers=headers, json=data)
    if r.status_code == 200:
        result = r.json()
        try:
            content = result["choices"][0]["message"]["content"]
        except Exception:
            content = result
        return {"response": content}
    else:
        return {"error": r.text, "status": r.status_code}
