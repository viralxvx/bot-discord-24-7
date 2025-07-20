# 🧠 Integración de Puter.js y DeepSeek en VXbot (Discord + Railway + GitHub)

## ✅ Infraestructura actual

- **GitHub**: https://github.com/viralxvx/bot-discord-24-7/
- **Railway**: activo y desplegando microservicios
- **Redis**: para persistencia de estado
- **Canal Discord**: `VX-GPT` con ID `1371956689439559850`
- **Variable de entorno**: `CANAL_GPT_ID`

---

## ⚙️ Objetivo de esta integración

Crear un **microservicio llamado `vx-deepseek`**, alojado en la carpeta `/vx-deepseek`, que funcione de forma separada al bot principal.  
Este microservicio debe:

- Escuchar en el canal `VX-GPT`
- Detectar mensajes nuevos automáticamente (sin comandos)
- Enviar el mensaje al modelo `deepseek-chat` o `deepseek-reasoner` a través de Puter.js
- Responder públicamente en el canal

---

## 🧪 Modelos disponibles con Puter.js

Puter.js permite acceder **sin clave, sin backend y gratis** a los siguientes modelos:

### 🌐 Modelos OpenAI (gratis o sin API Key)
- `gpt-4.1`
- `gpt-4o`
- `gpt-4.5-preview`
- `gpt-4.1-nano`
- `o1`, `o3`, `o4` y versiones `mini/pro`

### 🎨 Imagen y visión
- `DALL-E` (text to image)
- `GPT-4o Vision` (image captioning)

### 🧠 DeepSeek
- `deepseek-chat`: generación de texto
- `deepseek-reasoner`: razonamiento complejo
- Soporte para *streaming* (respuestas largas en tiempo real)

---

## 🛠️ Puter.js: Código base para DeepSeek

### ✅ Texto simple (DeepSeek Chat)
```javascript
puter.ai.chat("Hola, ¿cómo estás?", {
    model: "deepseek-chat"
}).then(response => {
    document.write(response.message.content);
});
