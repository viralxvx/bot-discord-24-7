# mensajes/soporte_mensajes.py

import discord

MENSAJE_INTRO = discord.Embed(
    title="🎓 Bienvenido al Soporte de VXbot",
    description=(
        "En **VX** formamos creadores virales, estratégicos y rentables.\n"
        "Este canal te permite aprender a usar la plataforma sin ayuda humana.\n\n"
        "📌 Usa el menú abajo para explorar guías, resolver dudas o enviar sugerencias.\n"
        "💰 Nuestro objetivo: que aprendas a **viralizar y generar ingresos pasivos** con tu contenido."
    ),
    color=discord.Color.teal()
)

OPCIONES_MENU = [
    discord.SelectOption(label="📌 ¿Qué es Go Viral?", value="go_viral"),
    discord.SelectOption(label="💬 ¿Cómo publicar correctamente?", value="publicar"),
    discord.SelectOption(label="❌ Faltas e inactividad", value="faltas"),
    discord.SelectOption(label="🔎 ¿Por qué no me validaron?", value="validacion"),
    discord.SelectOption(label="🎯 Consejos para viralizar", value="consejos"),
    discord.SelectOption(label="📈 ¿Cómo generar ingresos pasivos?", value="ingresos"),
    discord.SelectOption(label="📫 Enviar una sugerencia", value="sugerencia"),
    discord.SelectOption(label="🙋 Solicitar ayuda humana", value="ayuda"),
    discord.SelectOption(label="📚 Leer más sobre VX", value="leer_mas")
]

EXPLICACIONES = {
    "go_viral": discord.Embed(
        title="📌 ¿Qué es Go Viral?",
        description="Es el canal donde publicas contenido para validación y viralización. Sigue las normas y formato.",
        color=discord.Color.blurple()
    ),
    "publicar": discord.Embed(
        title="💬 ¿Cómo publicar correctamente?",
        description="Tu publicación debe incluir valor, claridad y cumplir el formato: gancho + desarrollo + CTA.",
        color=discord.Color.green()
    ),
    "faltas": discord.Embed(
        title="❌ Sistema de Faltas e Inactividad",
        description="El sistema penaliza incumplimientos y falta de publicaciones. Puedes solicitar prórrogas.",
        color=discord.Color.red()
    ),
    "validacion": discord.Embed(
        title="🔎 ¿Por qué no me validaron?",
        description="Revisa si faltó estructura, claridad o impacto. Aprende y vuelve a intentarlo.",
        color=discord.Color.orange()
    ),
    "consejos": discord.Embed(
        title="🎯 Consejos para viralizar",
        description="Investiga ganchos virales, sé directo, usa emociones y fomenta la interacción.",
        color=discord.Color.purple()
    ),
    "ingresos": discord.Embed(
        title="📈 ¿Cómo generar ingresos pasivos?",
        description="VX te enseña a usar contenido para atraer público, ofrecer valor y monetizar cada 2 semanas.",
        color=discord.Color.gold()
    ),
    "ayuda": discord.Embed(
        title="🙋 Solicitar ayuda humana",
        description="Si agotaste todas las opciones, escribe a un moderador o crea un ticket en #📞contacto-staff.",
        color=discord.Color.greyple()
    ),
    "leer_mas": discord.Embed(
        title="📚 ¿Qué es VX y por qué existe?",
        description=(
            "**Viral 𝕏 | VX** es un sistema de formación para creadores digitales.\n\n"
            "Nuestra misión es:\n"
            "- Enseñar a viralizar con intención\n"
            "- Automatizar el proceso de aprendizaje\n"
            "- Ayudarte a generar **ingresos pasivos** con tu contenido\n"
            "- Construir tu marca personal con estrategia y libertad\n\n"
            "Aquí no vienes a pedir permiso. Vienes a dominar tu voz y tu futuro."
        ),
        color=discord.Color.teal()
    )
}
