import discord
from redis_database import get_redis_instance
from handlers.logs import registrar_log

redis = get_redis_instance()

async def actualizar_mensaje_faltas(canal: discord.TextChannel, usuario: discord.User, faltas: int, aciertos: int, estado: str):
    embed = discord.Embed(
        title=f"Registro de {usuario.name}",
        description=f"🟥 Faltas: **{faltas}**\n🟩 Aciertos: **{aciertos}**\n🔒 Estado: **{estado}**",
        color=discord.Color.red() if faltas > aciertos else discord.Color.green()
    )
    embed.set_footer(text=f"ID: {usuario.id}")
    
    mensaje_id_key = f"falta_msg:{usuario.id}"
    mensaje_id = redis.get(mensaje_id_key)

    try:
        if mensaje_id:
            try:
                mensaje_antiguo = await canal.fetch_message(int(mensaje_id))
                await mensaje_antiguo.edit(embed=embed)
            except discord.NotFound:
                nuevo = await canal.send(embed=embed)
                redis.set(mensaje_id_key, nuevo.id)
        else:
            nuevo = await canal.send(embed=embed)
            redis.set(mensaje_id_key, nuevo.id)
        
        await registrar_log(f"📤 Registro de faltas actualizado: {usuario.name} (Faltas: {faltas}, Aciertos: {aciertos})", categoria="faltas")

    except Exception as e:
        print(f"[ERROR] al actualizar mensaje de faltas: {e}")
