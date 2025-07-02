# state_management.py

import redis
import json
import asyncio
from datetime import datetime, timedelta

class RedisState:
    def __init__(self, host, port, db, password=None):
        self.r = redis.StrictRedis(host=host, port=port, db=db, password=password, decode_responses=True)
        print("Conectado a Redis:", self.r.ping()) # Verifica la conexión

    async def get_last_post_time(self, user_id: int) -> float:
        """Obtiene el timestamp de la última publicación del usuario."""
        timestamp = await asyncio.to_thread(self.r.get, f"last_post_time:{user_id}")
        return float(timestamp) if timestamp else 0.0

    async def set_last_post_time(self, user_id: int, timestamp: float):
        """Establece el timestamp de la última publicación del usuario."""
        await asyncio.to_thread(self.r.set, f"last_post_time:{user_id}", timestamp)

    async def get_inactivity_status(self, user_id: int) -> str:
        """Obtiene el estado de inactividad del usuario (none, first_ban, kicked)."""
        return await asyncio.to_thread(self.r.get, f"inactivity_status:{user_id}") or "none"

    async def set_inactivity_status(self, user_id: int, status: str):
        """Establece el estado de inactividad del usuario."""
        await asyncio.to_thread(self.r.set, f"inactivity_status:{user_id}", status)

    async def get_inactivity_ban_start(self, user_id: int) -> float:
        """Obtiene el timestamp del inicio del baneo por inactividad."""
        timestamp = await asyncio.to_thread(self.r.get, f"inactivity_ban_start:{user_id}")
        return float(timestamp) if timestamp else 0.0

    async def set_inactivity_ban_start(self, user_id: int, timestamp: float):
        """Establece el timestamp del inicio del baneo por inactividad."""
        await asyncio.to_thread(self.r.set, f"inactivity_ban_start:{user_id}", timestamp)

    async def delete_inactivity_ban_start(self, user_id: int):
        """Elimina el registro de inicio de baneo por inactividad."""
        await asyncio.to_thread(self.r.delete, f"inactivity_ban_start:{user_id}")

    # --- NUEVOS MÉTODOS PARA PRÓRROGAS ---
    async def get_inactivity_extension_end(self, user_id: int) -> float:
        """Obtiene el timestamp del fin de la prórroga de inactividad."""
        timestamp = await asyncio.to_thread(self.r.get, f"inactivity_extension_end:{user_id}")
        return float(timestamp) if timestamp else 0.0

    async def set_inactivity_extension_end(self, user_id: int, timestamp: float):
        """Establece el timestamp del fin de la prórroga de inactividad."""
        await asyncio.to_thread(self.r.set, f"inactivity_extension_end:{user_id}", timestamp)

    async def delete_inactivity_extension_end(self, user_id: int):
        """Elimina el registro de fin de prórroga."""
        await asyncio.to_thread(self.r.delete, f"inactivity_extension_end:{user_id}")

    async def get_last_proroga_reason(self, user_id: int) -> str:
        """Obtiene la última razón de prórroga del usuario."""
        return await asyncio.to_thread(self.r.get, f"last_proroga_reason:{user_id}") or "No especificada"

    async def set_last_proroga_reason(self, user_id: int, reason: str):
        """Establece la última razón de prórroga del usuario."""
        await asyncio.to_thread(self.r.set, f"last_proroga_reason:{user_id}", reason)

    # --- NUEVOS MÉTODOS PARA TARJETAS DE FALTAS DINÁMICAS ---
    async def get_user_fault_card_message_id(self, user_id: int) -> int:
        """Obtiene el ID del mensaje de la tarjeta de faltas del usuario en #faltas."""
        msg_id = await asyncio.to_thread(self.r.get, f"faltas:user_card_message_id:{user_id}")
        return int(msg_id) if msg_id else None

    async def set_user_fault_card_message_id(self, user_id: int, message_id: int):
        """Establece el ID del mensaje de la tarjeta de faltas del usuario."""
        await asyncio.to_thread(self.r.set, f"faltas:user_card_message_id:{user_id}", message_id)

    async def delete_user_fault_card_message_id(self, user_id: int):
        """Elimina el ID del mensaje de la tarjeta de faltas del usuario."""
        await asyncio.to_thread(self.r.delete, f"faltas:user_card_message_id:{user_id}")

    async def get_all_fault_card_message_ids(self) -> dict[str, str]:
        """Obtiene todos los mapeos de user_id a message_id de las tarjetas de faltas."""
        keys = await asyncio.to_thread(self.r.keys, "faltas:user_card_message_id:*")
        # Extract user_id from keys, e.g., "faltas:user_card_message_id:123" -> "123"
        return {k.split(':')[-1]: await asyncio.to_thread(self.r.get, k) for k in keys}

    async def clear_all_fault_card_message_ids(self):
        """Elimina todas las entradas de tarjetas de faltas de Redis."""
        keys = await asyncio.to_thread(self.r.keys, "faltas:user_card_message_id:*")
        if keys:
            await asyncio.to_thread(self.r.delete, *keys)

    # --- NUEVO MÉTODO PARA MENSAJE PRINCIPAL DE SOPORTE ---
    async def get_soporte_menu_message_id(self) -> int:
        """Obtiene el ID del mensaje del menú de soporte en #soporte."""
        msg_id = await asyncio.to_thread(self.r.get, "soporte:menu_message_id")
        return int(msg_id) if msg_id else None

    async def set_soporte_menu_message_id(self, message_id: int):
        """Establece el ID del mensaje del menú de soporte en #soporte."""
        await asyncio.to_thread(self.r.set, "soporte:menu_message_id", message_id)

    # --- NUEVO MÉTODO PARA MENSAJE PRINCIPAL DE FALTAS ---
    async def get_faltas_panel_message_id(self) -> int:
        """Obtiene el ID del mensaje del panel de faltas en #faltas."""
        msg_id = await asyncio.to_thread(self.r.get, "faltas:panel_message_id")
        return int(msg_id) if msg_id else None

    async def set_faltas_panel_message_id(self, message_id: int):
        """Establece el ID del mensaje del panel de faltas en #faltas."""
        await asyncio.to_thread(self.r.set, "faltas:panel_message_id", message_id)
