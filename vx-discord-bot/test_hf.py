import os
import requests

HF_TOKEN = os.environ["HF_TOKEN"]
MODEL = "moonshotai/Kimi-K2-Instruct"

endpoint = "https://api.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json",
}
data = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "Crea un hilo viral para X de 11 posts."}
    ],
    "max_tokens": 400,
    "temperature": 0.7,
    "stream": False,
}

response = requests.post(endpoint, headers=headers, json=data)
print(response.status_code)
print(response.text)
