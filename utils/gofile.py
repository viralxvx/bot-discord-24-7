# utils/gofile.py

import aiohttp

async def subir_a_gofile(nombre_archivo, ruta):
    url = "https://api.gofile.io/uploadFile"
    async with aiohttp.ClientSession() as session:
        with open(ruta, "rb") as f:
            data = aiohttp.FormData()
            data.add_field("file", f, filename=nombre_archivo)
            async with session.post(url, data=data) as resp:
                respuesta = await resp.json()
                return respuesta.get("data", {}).get("downloadPage", "")
