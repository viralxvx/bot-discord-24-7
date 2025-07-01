import redis
import os
import discord # Importar discord para WebhookType

class RedisState:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            print(f"Conectado a Redis: {redis_url}")
        else:
            # Fallback for local development if REDIS_URL is not set
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=int(os.getenv('REDIS_DB', 0)),
                    password=os.getenv('REDIS_PASSWORD'),
                    decode_responses=True
                )
                print(f"Conectado a Redis: redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")
            except Exception as e:
                print(f"Error al conectar a Redis localmente: {e}. Asegúrate de que Redis esté corriendo o REDIS_URL esté configurado en Railway.")
                self.redis_client = None # O manejar de otra forma, ej. salir

    def get_last_post_time(self, user_id):
        return self.redis_client.get(f"last_post_time:{user_id}")

    def save_post(self, message_id, author_id, channel_id, url, author_name):
        post_data = {
            "message_id": message_id,
            "author_id": author_id,
            "url": url,
            "timestamp": discord.utils.utcnow().timestamp(),
            "author_name": author_name
        }
        self.redis_client.rpush(f"recent_posts:{channel_id}", json.dumps(post_data))
        # Keep only the last N posts, e.g., 50
        self.redis_client.ltrim(f"recent_posts:{channel_id}", -50, -1)
        self.redis_client.set(f"last_post_time:{author_id}", discord.utils.utcnow().timestamp())

    def get_recent_posts(self, channel_id):
        posts = self.redis_client.lrange(f"recent_posts:{channel_id}", 0, -1)
        return [json.loads(p) for p in posts]

    def has_reaction(self, user_id, message_id):
        # Verifica si el usuario ya reaccionó al mensaje específico
        return self.redis_client.sismember(f"reactions:{message_id}", user_id)

    def save_reaction(self, user_id, message_id):
        # Guarda que el usuario ha reaccionado a este mensaje
        self.redis_client.sadd(f"reactions:{message_id}", user_id)

    def get_required_reactions_details(self, current_user_id, channel_id):
        all_recent_posts = self.get_recent_posts(channel_id)
        
        # Filtra solo los posts de otros usuarios
        other_users_posts = [p for p in all_recent_posts if str(p['author_id']) != str(current_user_id)]
        
        # Encuentra el último post del usuario actual (si existe)
        current_user_last_post_timestamp = None
        for p in reversed(all_recent_posts):
            if str(p['author_id']) == str(current_user_id):
                current_user_last_post_timestamp = p['timestamp']
                break

        if current_user_last_post_timestamp is None:
            # Si el usuario actual no ha publicado todavía, no hay reacciones requeridas.
            return []

        # Los posts de otros que son posteriores al último post del usuario actual
        # y que el usuario actual aún no ha reaccionado.
        required_to_react = []
        for post in other_users_posts:
            if post['timestamp'] > current_user_last_post_timestamp:
                if not self.has_reaction(current_user_id, post['message_id']):
                    required_to_react.append(post)
        
        return required_to_react
    
    def set_welcome_message_id(self, message_id, channel_id):
        """Guarda el ID del mensaje de bienvenida activo para un canal."""
        self.redis_client.set(f"welcome_message_active:{channel_id}", message_id)

    def get_welcome_message_id(self, channel_id):
        """Obtiene el ID del mensaje de bienvenida activo para un canal."""
        return self.redis_client.get(f"welcome_message_active:{channel_id}")

    async def get_or_create_webhook(self, channel):
        webhook_id = self.redis_client.get(f"webhook_id:{channel.id}")
        webhook_token = self.redis_client.get(f"webhook_token:{channel.id}")

        if webhook_id and webhook_token:
            try:
                # Try to fetch existing webhook
                webhook = discord.Webhook.partial(id=int(webhook_id), token=webhook_token, adapter=discord.AsyncWebhookAdapter(timeout=1))
                await webhook.fetch() # Test if it's still valid
                return webhook
            except (discord.NotFound, discord.HTTPException):
                print(f"Webhook {webhook_id} not found or invalid, creating new one for channel {channel.name}.")
                # Webhook might have been deleted or token invalidated, create new one
                pass

        # If no webhook found in Redis or fetching failed, create a new one
        try:
            # Find an existing bot-owned webhook in the channel
            existing_webhooks = await channel.webhooks()
            for wh in existing_webhooks:
                if wh.user == channel.guild.me and wh.name == "Go-Viral-Bot-Webhook":
                    webhook = wh
                    break
            else:
                # No existing bot-owned webhook, create a new one
                webhook = await channel.create_webhook(name="Go-Viral-Bot-Webhook")

            self.redis_client.set(f"webhook_id:{channel.id}", webhook.id)
            self.redis_client.set(f"webhook_token:{channel.id}", webhook.token)
            return webhook
        except discord.Forbidden:
            print(f"ERROR: No tengo permisos para gestionar webhooks en el canal '{channel.name}'.")
            return None
        except Exception as e:
            print(f"ERROR al obtener o crear webhook para el canal '{channel.name}': {e}")
            return None
