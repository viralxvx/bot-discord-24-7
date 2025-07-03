async def setup(bot):
    extensiones = [
        "comandos.estado",
        "comandos.estadisticas"
    ]

    for ext in extensiones:
        try:
            await bot.load_extension(ext)
            print(f"✅ Comando cargado: {ext}")
        except Exception as e:
            print(f"❌ Error al cargar {ext}: {type(e).__name__}: {e}")
