@bot.event
async def on_ready():
    print("Bot está listo, intentando enviar mensaje de bienvenida...")
    channel = bot.get_channel(1353824447131418676)  # ID del canal go-viral
    if not channel:
        print("Error: No se encontró el canal con ID 1353824447131418676")
        return

    print(f"Canal encontrado: {channel.name} (ID: {channel.id})")
    try:
        # Obtener mensajes fijados
        pinned_messages = await channel.pins()
        print(f"Número de mensajes fijados: {len(pinned_messages)}")

        # Desfijar mensajes de bienvenida anteriores
        for msg in pinned_messages:
            if "Bienvenido a go-viral" in msg.content:
                try:
                    await msg.unpin()
                    print(f"Mensaje de bienvenida antiguo desfijado: ID {msg.id}")
                    # Opcional: Eliminar el mensaje si no quieres que permanezca en el canal
                    await msg.delete()
                    print(f"Mensaje de bienvenida antiguo eliminado: ID {msg.id}")
                except discord.errors.Forbidden:
                    print(f"Error: No se pudo desfijar/eliminar mensaje ID {msg.id} por falta de permisos")
                except discord.errors.HTTPException as e:
                    print(f"Error HTTP al desfijar/eliminar mensaje ID {msg.id}: {e}")

        # Verificar si hay espacio para fijar un nuevo mensaje
        pinned_messages = await channel.pins()  # Actualizar lista después de desfijar
        if len(pinned_messages) >= 50:
            print("Límite de 50 mensajes fijados alcanzado")
            oldest_pinned = pinned_messages[-1]
            try:
                await oldest_pinned.unpin()
                print(f"Desfijado mensaje antiguo para hacer espacio: ID {oldest_pinned.id}")
            except discord.errors.Forbidden:
                print(f"Error: No se pudo desfijar mensaje ID {oldest_pinned.id} por falta de permisos")
                return
            except discord.errors.HTTPException as e:
                print(f"Error HTTP al desfijar mensaje ID {oldest_pinned.id}: {e}")
                return

        # Enviar el nuevo mensaje de bienvenida
        welcome_message = await channel.send(
            "📢 **Bienvenido a go-viral!** Por favor, sigue las reglas:\n"
            "1. Publica solo URLs en el formato `https://x.com/usuario/status/123456...`.\n"
            "2. Reacciona con 🔥 a las publicaciones de otros.\n"
            "3. Reacciona con 👍 a tu propia publicación en 120 segundos.\n"
            "¡Disfruta del canal!"
        )
        print(f"Mensaje de bienvenida enviado: ID {welcome_message.id}")

        # Fijar el mensaje
        await welcome_message.pin()
        print("Mensaje de bienvenida fijado exitosamente")
        await registrar_log(f"Mensaje de bienvenida enviado y fijado (ID: {welcome_message.id})", bot.user, channel)

    except discord.errors.Forbidden as e:
        print(f"Error de permisos al enviar/fijar el mensaje: {e}")
    except discord.errors.HTTPException as e:
        print(f"Error HTTP al enviar/fijar el mensaje: {e}")
    except Exception as e:
        print(f"Error inesperado al enviar/fijar el mensaje de bienvenida: {type(e).__name__}: {e}")
