import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.huggingface.co/v1",  # CORRECTO
    api_key=os.environ["HF_TOKEN"],
)

completion = client.chat.completions.create(
    model="moonshotai/Kimi-K2-Instruct",
    messages=[
        {
            "role": "user",
            "content": "creame un hilo viral para X de 11 post"
        }
    ],
)

print(completion.choices[0].message.content)
