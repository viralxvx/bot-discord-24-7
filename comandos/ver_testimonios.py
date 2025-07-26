# comandos/ver_testimonios.py

import discord
from discord import app_commands
from discord.ext import commands
from config import get_env_int
from utils.redis_conn import redis_conn
from utils.formatter import generar_estrellas, formatear_fecha

ADMIN_ROLE_ID = get_env_int("ADMIN_ROLE_ID")

class VerTestimonios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ver_testimonios", description="Revisa los testimonios recibidos (solo admins)")
    @app_commands.describe(pagina="Número de página (5 testimonios por página)")
    async def ver_testimonios(self, interaction: discord.Interaction, pagina: int = 1):
        await interaction.response.defer(ephemeral=True)

        if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.followup.send("❌ No tienes permiso para usar este comando.", ephemeral=True)
            return

        # Buscar todas las claves de testimonios
        keys = sorted(redis_conn.keys("vx:testimonio:*"))
        total = len(keys)
        por_pagina = 5
        inicio = (pagina - 1) * por_pagina
        fin = inicio + por_pagina

        if inicio >= total:
            await interaction.followup.send("❌ No hay testimonios en esa página.", ephemeral=True)
            return

        mensajes = []
        for k in keys[inicio:fin]:
            data = redis_conn.hgetall(k)
            autor_id = k.split(":")[-1]

            nombre = "Anónimo" if data.get("anonimo") == "True" else f"<@{autor_id}>"
            estrellas = generar_estrellas(int(data.get("calificacion", 5)))

            mensaje = (
                f"**{nombre}** · {estrellas}\n"
                f"🧠 *{data.get('contenido', '')}*\n"
                f"🕒 Tiempo: {data.get('tiempo', '—')} · 🚀 Impacto: {data.get('impacto', '—')}\n"
                f"💡 Más le gustó: {data.get('destacar', '—')}\n"
                f"📅 {formatear_fecha()}\n"
                f"───────────────────────────────"
            )
            mensajes.append(mensaje)

        embed = discord.Embed(
            title=f"📂 Página {pagina} de testimonios",
            description="\n".join(mensajes),
            color=0x5865F2
        )
        embed.set_footer(text=f"Total de testimonios: {total}")

        try:
            await interaction.user.send(embed=embed)
            await interaction.followup.send("📬 Te envié los testimonios por DM.", ephemeral=True)
        except:
            await interaction.followup.send("❌ No pude enviarte DM. Activa los mensajes directos del servidor.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(VerTestimonios(bot))
