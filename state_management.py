import redis
import os
import json
import time
import datetime # Importar datetime

class RedisState:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        print(f"Conectado a Redis: {redis_url}")

    def is_welcome_message_active(self, channel_id):
        return self.redis_client.exists(f"welcome_message_active:{channel_id}")

    def set_welcome_message_id(self, message_id, channel_id):
        self.redis_client.setex(f"welcome_message_active:{channel_id}", 86400, message_id) # 24 horas

    # Modificado: Ahora guarda content y url del mensaje
    def save_post(self, message_id, author_id, channel_id, message_content, author_name):
        post_data = {
            "message_id": str(message_id), # Asegura que sea string para JSON
            "author_id": str(author_id),
            "author_name": author_name, # Nuevo: nombre del autor
            "timestamp": time.time(),
            "channel_id": str(channel_id),
            "content": message_content,
            "url": f"https://discord.com/channels/{channel_id}/{message_id}" # URL de salto
        }
        self.redis_client.lpush(f"recent_posts:{channel_id}", json.dumps(post_data))
        self.redis_client.ltrim(f"recent_posts:{channel_id}", 0, 99) # Mantener los últimos 100 posts

        self.redis_client.set(f"last_post_time:{author_id}", time.time())
        self.redis_client.set(f"last_post_message_id:{author_id}", message_id)

    def get_recent_posts(self, channel_id):
        posts = self.redis_client.lrange(f"recent_posts:{channel_id}", 0, -1)
        return [json.loads(p) for p in posts]

    def get_last_post_time(self, author_id):
        last_post_time = self.redis_client.get(f"last_post_time:{author_id}")
        return float(last_post_time) if last_post_time else None
    
    def save_reaction(self, user_id, message_id):
        # Almacena una reacción de un usuario a un mensaje.
        # Usa un set para cada usuario para registrar a qué mensajes ha reaccionado.
        # Esto es útil para verificar si un usuario ha reaccionado a todos los posts requeridos.
        self.redis_client.sadd(f"reacted_posts:{user_id}", str(message_id))

    def has_reaction(self, user_id, message_id):
        # Verifica si un usuario ha reaccionado a un mensaje específico.
        return self.redis_client.sismember(f"reacted_posts:{user_id}", str(message_id))

    # Nuevo método para obtener los detalles de los posts que requieren reacción 🔥
    def get_required_reactions_details(self, user_id, channel_id):
        recent_posts = self.get_recent_posts(channel_id)
        
        # Filtra los posts a los que el usuario NO DEBE reaccionar (sus propios posts)
        # y los posts que el usuario YA ha reaccionado con 🔥
        
        # Primero, obtenemos el ID del último post que el usuario publicó,
        # para identificar todos los posts *posteriores a ese* que requieren reacción.
        last_post_message_id = self.redis_client.get(f"last_post_message_id:{user_id}")
        
        # Ordenar posts por timestamp ascendente para procesar cronológicamente
        recent_posts.sort(key=lambda x: x['timestamp'])

        required_posts_details = []
        found_last_user_post = False

        for post in recent_posts:
            # Si encontramos el último post del usuario, todos los siguientes son requeridos (si no son suyos)
            if str(post['message_id']) == last_post_message_id:
                found_last_user_post = True
                continue # No incluir su propio post en la lista de requeridos

            if found_last_user_post:
                # Solo añadir posts de otros usuarios que el usuario aún no ha reaccionado
                if str(post['author_id']) != str(user_id) and not self.has_reaction(user_id, post['message_id']):
                    required_posts_details.append({
                        'message_id': post['message_id'],
                        'url': post['url'],
                        'author_name': post['author_name'],
                        'content': post['content'] # Se puede usar para más contexto
                    })
        return required_posts_details

    # Método para limpiar el registro de reacciones de un usuario a posts antiguos (opcional, para mantener Redis limpio)
    # def clean_old_reactions(self, user_id, channel_id):
    #     # Implementar lógica para remover reacciones a posts muy antiguos o no válidos
    #     pass

    # Nuevo método para obtener o crear un webhook (Punto 7)
    async def get_or_create_webhook(self, channel):
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.name == "GoViralHook": # Usamos un nombre específico para nuestro webhook
                return webhook
        # Si no existe, crearlo
        webhook = await channel.create_webhook(name="GoViralHook")
        return webhook
