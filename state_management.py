import redis.asyncio as redis # Importante: usar redis.asyncio para async
import os
import discord # Importar discord para discord.utils.utcnow()
import json # Importar json para manejar datos de posts

class RedisState:
    def __init__(self, redis_url: str): # ¡CORRECCIÓN CLAVE AQUÍ! Ahora espera redis_url
        self.redis_client = None
        self.redis_url = redis_url # Guarda la URL pasada
        
        try:
            # Aquí se inicializa el cliente asíncrono
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # No se puede hacer ping síncrono aquí si redis_client es async.
            # La prueba de conexión se hará en el primer uso de un comando async,
            # o si se añade un método 'connect' aparte que sea async.
            print("Cliente Redis asíncrono inicializado.")
        except Exception as e:
            print(f"Error al inicializar cliente Redis con URL '{self.redis_url}': {e}")
            raise # Lanza el error para que el bot no inicie si Redis falla

    # Todos los métodos que interactúan con Redis deben ser async
    async def get_last_post_time(self, user_id):
        last_time = await self.redis_client.get(f"last_post_time:{user_id}")
        return float(last_time) if last_time else None

    async def set_last_post_time(self, user_id, timestamp):
        await self.redis_client.set(f"last_post_time:{user_id}", timestamp)

    async def save_post(self, message_id, author_id, channel_id, content, author_name):
        post_data = {
            'message_id': str(message_id),
            'author_id': str(author_id),
            'channel_id': str(channel_id),
            'content': content,
            'timestamp': discord.utils.utcnow().timestamp(),
            'author_name': author_name
        }
        post_json = json.dumps(post_data)
        await self.redis_client.set(f"post:{message_id}", post_json)
        list_key = f"recent_posts:{channel_id}"
        await self.redis_client.lpush(list_key, post_json)
        await self.redis_client.ltrim(list_key, 0, 49)

    async def get_recent_posts(self, channel_id):
        posts = await self.redis_client.lrange(f"recent_posts:{channel_id}", 0, -1)
        return [json.loads(p) for p in posts]

    async def save_reaction(self, user_id, message_id):
        await self.redis_client.sadd(f"reacted_users:{message_id}", str(user_id))

    async def has_reaction(self, user_id, message_id):
        return await self.redis_client.sismember(f"reacted_users:{message_id}", str(user_id))
    
    async def get_posts_by_author(self, author_id, channel_id):
        all_recent_posts = await self.get_recent_posts(channel_id)
        return [p for p in all_recent_posts if str(p['author_id']) == str(author_id)]

    async def get_required_reactions_details(self, author_id, channel_id):
        recent_posts = await self.get_recent_posts(channel_id)
        required_reactions = []
        for post in recent_posts:
            # Asegurarse de que GUILD_ID esté disponible, quizás pasarlo en el constructor del bot o RedisState si es muy crítico.
            # Por ahora, se sigue obteniendo de os.getenv.
            guild_id = os.getenv('GUILD_ID') 
            if str(post['author_id']) != str(author_id) and not await self.has_reaction(author_id, post['message_id']):
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
        return required_reactions[:2]

    async def set_welcome_message_id(self, message_id, channel_id):
        await self.redis_client.set(f"welcome_message_active:{channel_id}", str(message_id))

    async def get_welcome_message_id(self, channel_id):
        message_id = await self.redis_client.get(f"welcome_message_active:{channel_id}")
        return int(message_id) if message_id else None

    async def get_or_create_webhook(self, channel):
        webhook_key = f"webhook:{channel.id}"
        webhook_url = await self.redis_client.get(webhook_key)

        if webhook_url:
            try:
                # Asegúrate de pasar el cliente del bot al webhook
                # channel.guild.client es una forma, si no, puedes pasar self.bot al webhook desde GoViralCog
                webhook = discord.Webhook.from_url(webhook_url, client=channel.guild.client) 
                await webhook.fetch()
                return webhook
            except (discord.NotFound, discord.HTTPException):
                print(f"Webhook en Redis para el canal {channel.name} no válido o no encontrado. Creando uno nuevo...")
                await self.redis_client.delete(webhook_key)

        new_webhook = await channel.create_webhook(name=f"{channel.name}-go-viral-bot")
        await self.redis_client.set(webhook_key, new_webhook.url)
        print(f"Nuevo webhook creado para el canal {channel.name}")
        return new_webhook

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
            print("Conexión a Redis cerrada.")
