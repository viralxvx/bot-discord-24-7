# state_management.py
import redis.asyncio as redis
import json
import asyncio

class RedisState:
    def __init__(self, redis_url: str): # Cambiamos los parámetros a solo redis_url
        self.redis_url = redis_url
        self.redis_client = None

    async def connect(self):
        """Establece la conexión con Redis."""
        try:
            # Usar redis.from_url para parsear la URL completa
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            print("Conexión a Redis establecida con éxito.")
        except redis.ConnectionError as e:
            print(f"Error al conectar a Redis: {e}")
            raise # Re-lanza la excepción para que el bot no inicie si Redis falla

    async def close(self):
        """Cierra la conexión con Redis."""
        if self.redis_client:
            await self.redis_client.close()
            print("Conexión a Redis cerrada.")

    async def set_user_data(self, user_id: int, data: dict):
        """Guarda los datos de un usuario."""
        await self.redis_client.set(f"user_data:{user_id}", json.dumps(data))

    async def get_user_data(self, user_id: int) -> dict:
        """Obtiene los datos de un usuario."""
        data = await self.redis_client.get(f"user_data:{user_id}")
        return json.loads(data) if data else {}

    async def delete_user_data(self, user_id: int):
        """Elimina los datos de un usuario."""
        await self.redis_client.delete(f"user_data:{user_id}")

    # Métodos para la gestión de inactividad
    async def set_last_post_time(self, user_id: int, timestamp: int):
        await self.redis_client.hset("last_post_times", str(user_id), str(timestamp))

    async def get_last_post_time(self, user_id: int) -> int | None:
        timestamp = await self.redis_client.hget("last_post_times", str(user_id))
        return int(timestamp) if timestamp else None

    async def get_all_last_post_times(self) -> dict:
        data = await self.redis_client.hgetall("last_post_times")
        return {int(uid): int(ts) for uid, ts in data.items()}

    async def remove_last_post_time(self, user_id: int):
        await self.redis_client.hdel("last_post_times", str(user_id))

    # Métodos para la gestión de faltas
    async def get_fault_card_message_id(self, user_id: int) -> int | None:
        """Obtiene el ID del mensaje de la tarjeta de faltas de un usuario."""
        message_id = await self.redis_client.hget("fault_card_messages", str(user_id))
        return int(message_id) if message_id else None

    async def set_fault_card_message_id(self, user_id: int, message_id: int):
        """Guarda el ID del mensaje de la tarjeta de faltas de un usuario."""
        await self.redis_client.hset("fault_card_messages", str(user_id), str(message_id))

    async def remove_fault_card_message_id(self, user_id: int):
        """Elimina el ID del mensaje de la tarjeta de faltas de un usuario."""
        await self.redis_client.hdel("fault_card_messages", str(user_id))

    async def get_all_fault_card_message_ids(self) -> dict:
        """Obtiene todos los IDs de mensajes de tarjetas de faltas."""
        data = await self.redis_client.hgetall("fault_card_messages")
        return {int(uid): int(mid) for uid, mid in data.items()}

    # Métodos para la gestión de prórrogas
    async def set_proroga_info(self, user_id: int, end_timestamp: int, reason: str, aproved_by_id: int, message_id: int):
        """Guarda la información de una prórroga para un usuario."""
        proroga_data = {
            "end_timestamp": end_timestamp,
            "reason": reason,
            "aproved_by_id": aproved_by_id,
            "message_id": message_id # ID del mensaje de solicitud de prórroga
        }
        await self.redis_client.set(f"proroga:{user_id}", json.dumps(proroga_data))

    async def get_proroga_info(self, user_id: int) -> dict | None:
        """Obtiene la información de la prórroga de un usuario."""
        data = await self.redis_client.get(f"proroga:{user_id}")
        return json.loads(data) if data else None

    async def delete_proroga_info(self, user_id: int):
        """Elimina la información de la prórroga de un usuario."""
        await self.redis_client.delete(f"proroga:{user_id}")

    async def get_all_proroga_infos(self) -> dict:
        """Obtiene la información de todas las prórrogas activas."""
        # Esto requiere escanear claves, lo cual puede ser costoso en bases de datos grandes
        # Para Railway, que gestiona claves por prefijo, esto es común.
        prorogas = {}
        async for key in self.redis_client.scan_iter("proroga:*"):
            user_id = int(key.split(":")[1])
            data = await self.redis_client.get(key)
            if data:
                prorogas[user_id] = json.loads(data)
        return prorogas

    async def set_last_panel_update_time(self, timestamp: int):
        """Guarda el último timestamp de actualización del panel de faltas."""
        await self.redis_client.set("last_panel_update_time", str(timestamp))

    async def get_last_panel_update_time(self) -> int | None:
        """Obtiene el último timestamp de actualización del panel de faltas."""
        timestamp = await self.redis_client.get("last_panel_update_time")
        return int(timestamp) if timestamp else None
