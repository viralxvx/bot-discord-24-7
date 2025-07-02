# config.py

import os

# --- Configuración del Bot ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# --- IDs de Canales ---
CANAL_GO_VIRAL_ID = 1353824447131418676 # Reemplaza con el ID de tu canal Go Viral
CANAL_FALTAS_ID = 1388891883551326298   # Reemplaza con el ID de tu canal de faltas
CANAL_SOPORTE_ID = 1376744723665911894  # Reemplaza con el ID de tu canal de soporte
CANAL_LOGS_ID = 1388347584061374514     # Reemplaza con el ID de tu canal de logs

# --- IDs de Roles ---
ROLE_MODERADOR_ID = 1389761947062505502 # Reemplaza con el ID del rol de Moderador/Administrador

# --- Configuración de Redis ---
REDIS_URL = os.getenv("REDIS_URL")

# --- Configuración del Sistema Go Viral (Ya existentes, confirmadas) ---
MIN_REACCIONES_GO_VIRAL = 5           # Número de reacciones únicas necesarias para volverse viral
TIEMPO_ESPERA_POST_MINUTOS = 24 * 60  # 24 horas en minutos (tiempo de espera entre posts del mismo usuario)

# --- Reglas de Inactividad (Ya existentes) ---
DIAS_INACTIVIDAD_PARA_BAN = 3      # Número de días sin publicar para que un usuario reciba su primer baneo temporal
DURACION_BAN_DIAS = 7              # Duración del baneo temporal en días (ej. 7 para 7 días)

# --- Reglas de Prórrogas (Ya existentes) ---
MAX_PRORROGA_DAYS = 30             # Duración máxima que un usuario puede solicitar para una prórroga en días
DIAS_PRE_AVISO_PRORROGA = 2        # Días antes de que expire una prórroga para enviar un mensaje directo (DM) de aviso al usuario

# --- Contenido y ID del Mensaje Fijo del Canal #faltas (Ya existentes) ---
FALTAS_PANEL_MESSAGE_ID = None 
FALTAS_PANEL_CONTENT = (
    "**__Panel de Control de Actividad GoViral__**\n"
    "Este canal muestra el estado de actividad y el historial de faltas de los miembros de la comunidad GoViral.\n"
    "Cada mensaje es una 'tarjeta' de usuario que se actualiza automáticamente. "
    "Los usuarios expulsados son eliminados de este panel.\n\n"
    "✅ = Activo | ⚠️ = Falta Menor | ⏳ = Prórroga | ⛔️ = Baneado | ❌ = Expulsado (eliminado del panel)\n\n"
    "--- (Las tarjetas de usuario aparecerán debajo de este mensaje) ---"
)

# --- Contenido y ID del Mensaje Fijo del Canal #soporte (Ya existentes) ---
SOPORTE_MENU_MESSAGE_ID = None 
SOPORTE_MENU_CONTENT = (
    "👋 **Bienvenido al Centro de Soporte de GoViral!**\n\n"
    "Aquí puedes realizar diversas gestiones y solicitudes. "
    "Usa el menú desplegable a continuación para elegir la opción que necesites:\n\n"
)

# --- Configuración del Mensaje de Bienvenida del Canal Go Viral (¡NUEVO!) ---
WELCOME_MESSAGE_TITLE = "🧵 REGLAS DEL CANAL GO-VIRAL 🧵"
WELCOME_MESSAGE_IMAGE_URL = "https://drive.google.com/uc?export=download&id=1LGwse5dI_Q_PpQhhfpLBudteATKoy4Hj"
WELCOME_MESSAGE_TEXT = """
## 🎉 **¡BIENVENIDOS A GO-VIRAL!** 🎉
¡Nos alegra tenerte aquí! Este es tu espacio para hacer crecer tu contenido de **𝕏 (Twitter)** junto a nuestra increíble comunidad.
## 🎯 **OBJETIVO**
Compartir contenido de calidad de **𝕏 (Twitter)** siguiendo un sistema organizado de apoyo mutuo.
---
## 📋 **REGLAS PRINCIPALES**
### 🔗 **1. FORMATO DE PUBLICACIÓN**
✅ **FORMATO CORRECTO:**
https://x.com/miguelrperaltaf/status/1931928250735026238
❌ **FORMATO INCORRECTO:**
https://x.com/miguelrperaltaf/status/1931928250735026238?s=46&t=m7qBPHFiZFqks3K1jSaVJg

**📝 NOTA:** El bot corregirá automáticamente los enlaces mal formateados, pero es mejor aprender el formato correcto.
### 👍 **2. VALIDACIÓN DE TU POST**
- Reacciona con **👍** a tu propia publicación
- **⏱️ Tiempo límite:** 120 segundos
- Sin reacción = eliminación automática
### 🔥 **3. APOYO A LA COMUNIDAD**
Antes de publicar nuevamente:
- Reacciona con **🔥** a TODAS las publicaciones posteriores a tuya
- **REQUISITO:** Apoya primero en **𝕏** con RT + LIKE + COMENTARIO
- Luego reacciona con 🔥 en Discord
### ⏳ **4. INTERVALO ENTRE PUBLICACIONES**
- Espera mínimo **2 publicaciones válidas** de otros usuarios
- No hay límite de tiempo, solo orden de turnos
---
## ⚠️ **SISTEMA DE FALTAS**
### 🚨 **Infracciones que generan falta:**
- Formato incorrecto de URL
- No reaccionar con 👍 a tiempo
- Publicar sin haber apoyado posts anteriores
- Usar 🔥 en tu propia publicación
- No respetar el intervalo de publicaciones
### 📊 **Consecuencias:**
- Registro en canal de faltas
- Notificación por DM
- Posibles sanciones según historial
---
## 🤖 **AUTOMATIZACIÓN DEL BOT**
- ✅ Corrección automática de URLs mal formateadas
- 🗑️ Eliminación de publicaciones inválidas
- 📬 Notificaciones temporales (15 segundos)
- 📝 Registro completo en logs
- 💬 Mensajes privados informativos
---
## 🏆 **CONSEJOS PARA EL ÉXITO**
1.  **Lee las reglas** antes de participar
2.  **Apoya genuinamente** en 𝕏 antes de reaccionar
3.  **Mantén el formato** exacto de URLs
4.  **Sé constante** con las reacciones
5.  **Respeta los turnos** de otros usuarios
---
## 📞 **¿DUDAS?**
Revisa el historial del canal o consulta en el canal soporte.
**¡Juntos hacemos crecer nuestra comunidad! 🚀**
---
*Bot actualizado • Sistema automatizado • Apoyo 24/7*
"""
