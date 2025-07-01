import redis
import os
import discord # Importar discord para WebhookType
import json # Importar json para manejar datos de posts

class RedisState:
    def __init__(self):
        self.redis_client = self._get_redis_client()

    def _get_redis_client(self):
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            raise ValueError("REDIS_URL no está configurada en las variables de entorno.")
        
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            # Prueba la conexión
            client.ping()
            print("Conectado a Redis exitosamente.")
            return client
        except redis.exceptions.ConnectionError as e:
            print(f"Error al conectar a Redis: {e}")
            raise

    def get_last_post_time(self, user_id):
        """
        Obtiene la última marca de tiempo de publicación de un usuario.
        """
        last_time = self.redis_client.get(f"last_post_time:{user_id}")
        return float(last_time) if last_time else None

    def set_last_post_time(self, user_id, timestamp):
        """
        Establece la última marca de tiempo de publicación para un usuario.
        """
        self.redis_client.set(f"last_post_time:{user_id}", timestamp)

    def save_post(self, message_id, author_id, channel_id, content, author_name):
        """
        Guarda una publicación en Redis y la añade a la lista de posts recientes del canal.
        """
        post_data = {
            'message_id': str(message_id),
            'author_id': str(author_id),
            'channel_id': str(channel_id),
            'content': content,
            'timestamp': discord.utils.utcnow().timestamp(),
            'author_name': author_name # Guardar el nombre del autor
        }
        post_json = json.dumps(post_data)
        
        # Guardar post individualmente
        self.redis_client.set(f"post:{message_id}", post_json)
        
        # Añadir a la lista de posts recientes del canal (limitado a los últimos 50 para no crecer indefinidamente)
        # Usamos LTRIM para mantener solo los últimos N elementos
        list_key = f"recent_posts:{channel_id}"
        self.redis_client.lpush(list_key, post_json)
        self.redis_client.ltrim(list_key, 0, 49) # Mantener solo los últimos 50 posts

    def get_recent_posts(self, channel_id):
        """
        Obtiene los posts recientes de un canal.
        """
        posts = self.redis_client.lrange(f"recent_posts:{channel_id}", 0, -1)
        return [json.loads(p) for p in posts]

    def save_reaction(self, user_id, message_id):
        """
        Marca que un usuario ha reaccionado a un mensaje con 🔥.
        """
        self.redis_client.sadd(f"reacted_users:{message_id}", str(user_id))

    def has_reaction(self, user_id, message_id):
        """
        Verifica si un usuario ha reaccionado a un mensaje con 🔥.
        """
        return self.redis_client.sismember(f"reacted_users:{message_id}", str(user_id))
    
    def get_posts_by_author(self, author_id, channel_id):
        """
        Obtiene las publicaciones de un autor específico en un canal.
        """
        all_recent_posts = self.get_recent_posts(channel_id)
        return [p for p in all_recent_posts if str(p['author_id']) == str(author_id)]

    def get_required_reactions_details(self, author_id, channel_id):
        """
        Obtiene detalles de los posts de otros usuarios a los que el autor actual debe reaccionar.
        Excluye posts del propio autor.
        """
        # Obtenemos los 10 posts más recientes del canal
        recent_posts = self.get_recent_posts(channel_id)
        
        # Filtramos para obtener solo los posts de otros usuarios, no los del autor_id actual
        # Y que el post haya sido publicado antes del post actual del autor (implícito por el orden de get_recent_posts)
        # y que el autor NO haya reaccionado ya
        
        required_reactions = []
        for post in recent_posts:
            if str(post['author_id']) != str(author_id) and not self.has_reaction(author_id, post['message_id']):
                # Construir una URL de salto para el mensaje si es posible
                guild_id = os.getenv('GUILD_ID') # Asumiendo que GUILD_ID está en tus variables de entorno
                if guild_id:
                    jump_url = f"https://discord.com/channels/{guild_id}/{post['channel_id']}/{post['message_id']}"
                else:
                    jump_url = "URL no disponible"

                required_reactions.append({
                    'message_id': post['message_id'],
                    'author_id': post['author_id'],
                    'author_name': post['author_name'],
                    'url': jump_url
                })
        # Devolver solo los últimos 2 posts a los que se debe reaccionar
        return required_reactions[:2]

    def set_welcome_message_id(self, message_id, channel_id):
        """
        Guarda el ID del mensaje de bienvenida activo en Redis.
        """
        self.redis_client.set(f"welcome_message_active:{channel_id}", str(message_id))

    def get_welcome_message_id(self, channel_id):
        """
        Obtiene el ID del mensaje de bienvenida activo de Redis.
        """
        message_id = self.redis_client.get(f"welcome_message_active:{channel_id}")
        return int(message_id) if message_id else None

    async def get_or_create_webhook(self, channel):
        webhook_key = f"webhook:{channel.id}"
        webhook_url = self.redis_client.get(webhook_key)

        if webhook_url:
            try:
                webhook = discord.Webhook.from_url(webhook_url, client=channel.guild.client) # Asegurarse de usar client del bot
                await webhook.fetch() # Intenta obtener para verificar si es válido
                return webhook
            except (discord.NotFound, discord.HTTPException):
                print(f"Webhook en Redis para el canal {channel.name} no válido o no encontrado. Creando uno nuevo...")
                self.redis_client.delete(webhook_key) # Eliminar webhook inválido

        # Si no existe o no es válido, crear uno nuevo
        new_webhook = await channel.create_webhook(name=f"{channel.name}-go-viral-bot")
        self.redis_client.set(webhook_key, new_webhook.url)
        print(f"Nuevo webhook creado para el canal {channel.name}")
        return new_webhook
