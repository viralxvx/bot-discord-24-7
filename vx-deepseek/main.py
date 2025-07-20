import os
import discord
import aiohttp
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
CANAL_GPT_ID = int(os.getenv("CANAL_GPT_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

PUTER_SCRIPT = "https://js.puter.com/v2/"
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><script src="{script}"></script></head>
<body>
<script>
(async () => {{
    const r = await puter.ai.chat("{prompt}", {{ model: "deepseek-chat" }});
    window.parent.postMessage(r, "*");
}})();
</script>
</body>
</html>
"""

async def generar_respuesta(prompt):
    html = HTML_TEMPLATE.format(script=PUTER_SCRIPT, prompt=prompt.replace('"', '\\"'))
    async with aiohttp.ClientSession() as session:
        async with session.post("https://html-render.puter.com", data=html.encode("utf-8")) as resp:
            if resp.status == 200:
                json = await resp.json()
                return json.get("text", "[Respuesta vacía]")
            else:
                return "[Error al generar respuesta]"

@client.event
async def on_ready():
    print(f"🤖 DeepSeek bot conectado como {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != CANAL_GPT_ID:
        return

    await message.channel.typing()
    respuesta = await generar_respuesta(message.content)
    await message.reply(respuesta)

client.run(TOKEN)
