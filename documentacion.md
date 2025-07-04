¡Aquí tienes la **documentación técnica** completamente actualizada con los últimos cambios para `#🧵go-viral` (sólo embeds, reglas adaptativas, control 9/2, mensajes profesionales, textos centralizados), lista para tu equipo y para moderadores!

---

# 📘 DOCUMENTACIÓN TÉCNICA — VXbot

Este documento resume todas las funcionalidades implementadas en **VXbot**, la infraestructura utilizada, automatizaciones, comandos activos y detalles técnicos relevantes para administración y desarrollo.

---

## 🚀 Infraestructura y tecnologías

* **Lenguaje**: Python 3.10+
* **Librería principal**: `discord.py v2.3.2`
* **Base de datos**: Redis (`redis==5.0.1`)
* **Deploy**: Railway (plan pago, always-on)
* **Gestión de secretos**: Variables de entorno en Railway
* **Estructura**: Modular (`canales/`, `comandos/`, `mensajes/`)
* **Persistencia total**: Redis (historial y estado nunca se pierden)

---

## 🧩 Funciones implementadas

### ✅ Canal `#👋preséntate`

* Mensaje de bienvenida profesional y educativo (embed)
* Menú con enlaces directos a:

  * 📖 `#guías`
  * ✅ `#normas-generales`
  * 🏆 `#victorias`
  * ♟ `#estrategias-probadas`
  * 🏋 `#entrenamiento`
* Solo el bot puede escribir

---

### ✅ Canal `#✅normas-generales`

* Limpia **todos** los mensajes (incluye fijados/antiguos)
* Publica normas en **dos embeds** elegantes (edita si ya existen)
* El canal es solo de lectura, el bot borra cualquier mensaje ajeno
* Normas centralizadas y editables desde `/mensajes/`

---

### ✅ Canal `#📤faltas` (Panel público de reputación)

* Un mensaje profesional por miembro (foto de perfil, estado, faltas, fecha/hora)
* Sin duplicados: si ya existe, se edita; si no, se crea; si expulsado, se borra
* Panel 100% sincronizado con el servidor al iniciar o reiniciar el bot

---

### ✅ Canal `#💻comandos`

* Exclusivo para comandos (`/estado`, `/estadisticas`, `/prorroga`)
* Borra mensajes antiguos al iniciar y muestra instrucciones de uso
* Solo ahí se aceptan comandos, la respuesta:

  * Se publica en el canal (**dura 10 minutos**)
  * Se envía por DM al usuario
* `/estadisticas` solo accesible a admins/mods

---

### ✅ Sistema de Faltas y Consultas

* Comandos `/estado` y `/estadisticas`:

  * **/estado**: cualquier usuario, muestra sus faltas, estado y advertencias
  * **/estadisticas**: solo admins/mods, muestra totales de miembros, baneados, expulsados

---

### ✅ Sistema de Baneo y Expulsión por Inactividad (100% automático)

* Si un usuario pasa **3 días sin publicar** en `#🧵go-viral`:

  * **Baneo automático** por 7 días (DM y log)
* Si reincide después del baneo:

  * **Expulsión permanente** (DM y log)
* Todos los eventos quedan en logs y se publican avisos en los canales correspondientes

---

### ✅ Sistema de Prórrogas de Inactividad

* **Usuarios normales**: pueden pedir prórroga de hasta 7 días enviando un mensaje en `#👨🔧soporte`

  * El bot concede prórroga automáticamente, borra el mensaje y envía confirmación por DM/canal
* **Admins/Mods**: pueden dar prórrogas ilimitadas vía comando `/prorroga` en `#💻comandos`

  * Mensaje de confirmación en canal y por DM

---

### ✅ Canal `#🧵go-viral` (100% automático, educativo y ADAPTATIVO)

* **Embed informativo fijo**: explica todas las reglas y funcionamiento, con imagen/logo y pie profesional (se actualiza centralizado)
* **Mensaje de bienvenida personalizado** (embed, solo la 1ª vez a cada usuario)
* **Validaciones automáticas y adaptativas en cada publicación:**

  * Corrige automáticamente enlaces mal formateados, simula publicación limpia, avisa por embed educativo (canal) y DM (embed)
  * Verifica que se reaccione con 👍 en 2 minutos o elimina (embed educativo + DM)
  * **No permite publicar** si no hay 2 posts válidos de otros miembros tras la última publicación del usuario (24h override: si pasan 24h, permite)
  * **Control de apoyo adaptativo**: requiere haber apoyado (🔥 en Discord) a los **9 anteriores** SOLO si hay suficiente volumen; si no, ajusta y exige apoyo a todos los disponibles
  * Mensajes educativos, avisos y bienvenidas siempre en embed (profesional), todo centralizado en `/mensajes/viral_texto.py`
  * Memoria persistente de quién ya recibió bienvenida (Redis)
* **Totalmente modular**: todos los textos y notificaciones son editables desde `/mensajes/viral_texto.py`

---

### ✅ Logs y depuración

* Cada acción clave genera logs visibles para Railway y (cuando aplica) en el canal de logs
* Todos los errores y eventos quedan registrados

---

## 🔧 Comandos slash activos

| Comando         | Quién puede usarlo | Dónde se usa | Respuesta                  |
| --------------- | ------------------ | ------------ | -------------------------- |
| `/estado`       | Todos los miembros | #💻comandos  | Estado y faltas personales |
| `/estadisticas` | Solo admins/mods   | #💻comandos  | Totales, estado general    |
| `/prorroga`     | Solo admins/mods   | #💻comandos  | Da prórroga a miembros     |

---

## 🧠 Aspectos técnicos destacados

* IDs y claves gestionadas solo por variables de entorno
* Toda la lógica (por canal/comando) separada de los textos/avisos (`mensajes/`)
* Todos los canales críticos (normas, comandos, faltas, viral) protegidos: solo el bot publica o responde
* Actualizaciones y mejoras no afectan lo ya funcional gracias al diseño modular
* Panel de faltas y reputación siempre actualizado, sin duplicados ni pérdidas
* Sistema de automatización y reglas adaptativas en `#🧵go-viral` centralizado y editable por admins (no requiere tocar código)

---

## 🔜 Próximos pasos (expansión)

* Módulo para automatizar soporte avanzado
* Integración con panel web o dashboard de reputación
* Registro ampliado en `#📝logs` y más comandos administrativos
* Automatización avanzada de publicaciones y anti-spam en `#🧵go-viral`

---

*Última actualización: 2025-07-04* / Hora 11:56 pm
