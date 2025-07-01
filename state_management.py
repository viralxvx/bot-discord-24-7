import redis
from config import REDIS_URL
import json

class RedisState:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL)
    
    def save_post(self, message_id, author_id, channel_id):
        self.client.hset(f"post:{message_id}", mapping={"author_id": author_id, "channel_id": channel_id})
    
    def get_last_post(self, author_id):
        posts = self.client.keys("post:*")
        for post in posts:
            data = self.client.hgetall(post)
            if int(data[b'author_id']) == author_id:
                return post
        return None
    
    def get_recent_posts(self, channel_id):
        posts = self.client.keys("post:*")
        return [self.client.hgetall(post) for post in posts if int(self.client.hget(post, "channel_id")) == channel_id]
    
    def save_reaction(self, user_id, message_id):
        self.client.sadd(f"reactions:{message_id}", user_id)
    
    def has_reaction(self, user_id, message_id):
        return self.client.sismember(f"reactions:{message_id}", user_id)
    
    def get_required_reactions(self, author_id, channel_id):
        posts = self.get_recent_posts(channel_id)
        last_post = self.get_last_post(author_id)
        if not last_post:
            return []
        return [p[b'id'] for p in posts if int(p[b'author_id']) != author_id]
    
    def increment_falta(self, user_id, motivo):
        self.client.hincrby(f"falta:{user_id}", "count", 1)
        self.client.hset(f"falta:{user_id}", "last_motivo", motivo)
    
    def get_faltas(self, user_id):
        return self.client.hgetall(f"falta:{user_id}")
    
    # ========== NUEVOS MÉTODOS PARA MENSAJE DE BIENVENIDA ==========
    
    def set_welcome_message_id(self, message_id, channel_id):
        """Guarda el ID del mensaje de bienvenida"""
        self.client.setex(f"welcome_msg:{channel_id}", 86400, message_id)  # Expira en 24 horas
    
    def get_welcome_message_id(self, channel_id):
        """Obtiene el ID del mensaje de bienvenida"""
        message_id = self.client.get(f"welcome_msg:{channel_id}")
        return int(message_id) if message_id else None
    
    def clear_welcome_message_id(self, channel_id):
        """Limpia la referencia del mensaje de bienvenida"""
        self.client.delete(f"welcome_msg:{channel_id}")
    
    def is_welcome_message_active(self, channel_id):
        """Verifica si hay un mensaje de bienvenida activo"""
        return self.client.exists(f"welcome_msg:{channel_id}")
    
    def get_all_welcome_messages(self):
        """Obtiene todos los mensajes de bienvenida activos (para debugging)"""
        keys = self.client.keys("welcome_msg:*")
        result = {}
        for key in keys:
            channel_id = key.decode().split(":")[-1]
            message_id = self.client.get(key)
            result[channel_id] = message_id.decode() if message_id else None
        return result
