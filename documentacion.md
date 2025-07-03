# 📘 DOCUMENTACIÓN TÉCNICA — VXbot

Este documento resume las funcionalidades implementadas en **VXbot**, infraestructura, automatizaciones, comandos activos y memoria técnica para moderadores/desarrolladores.

---

## 🚀 Infraestructura y tecnologías

- **Lenguaje**: Python 3.10+
- **Librería principal**: `discord.py v2.3.2`
- **Base de datos**: Redis (`redis==5.0.1`)
- **Deploy**: Railway (plan pago, siempre activo)
- **Gestión de secretos**: Variables de entorno (Railway)
- **Estructura**: Modular (`canales/`, `comandos/`, `mensajes/`)
- **Persistencia total**: Redis, nunca se pierde historial ni estado

---

## 🧩 Funciones implementadas

### ✅ Canal `#👋preséntate`
- Mensaje de bienvenida visual, profesional y educativo
- Menú con enlaces directos a:
  - 📖 `#guías`
  - ✅ `#normas-generales`
  - 🏆 `#victorias`
  - ♟ `#estrategias-probadas`
  - 🏋 `#entrenamiento`
- Solo el bot puede escribir

---

### ✅ Canal `#✅normas-generales`
- Limpia **todos** los mensajes (incluye fijados/antiguos)
- Publica normas en **dos embeds** elegantes (edita si ya existen)
- El canal es solo de lectura, el bot borra cualquier mensaje ajeno
- Normas centralizadas y editables desde `/mensajes/`

---

### ✅ Canal `#📤faltas` (Panel público de reputación)
- Un mensaje profesional por miembro (foto de perfil, estado, faltas, fecha/hora)
- No hay duplicados: si ya existe, se edita; si no, se crea; si expulsado, se borra
- Panel 100% sincronizado con el servidor al iniciar o reiniciar el bot

---

### ✅ Canal `#💻comandos`
- Exclusivo para comandos (`/estado`, `/estadisticas`, `/prorroga`)
- Borra mensajes antiguos al iniciar y muestra instrucciones de uso
- Solo ahí se aceptan comandos, la respuesta:
  - Se publica en el canal (**dura 10 minutos**)
  - Se envía por DM al usuario
- `/estadisticas` solo accesible a admins/mods

---

### ✅ Sistema de Faltas y Consultas
- Comandos `/estado` y `/estadisticas`:
  - **/estado**: cualquier usuario, muestra sus faltas, estado y advertencias
  - **/estadisticas**: solo admins, muestra totales de miembros, baneados, expulsados

---

### ✅ Sistema de Baneo y Expulsión por Inactividad (100% automático)
- Si un usuario pasa **3 días sin publicar** en `#🧵go-viral`:
  - Recibe **baneo automático** por 7 días (DM y log)
- Si reincide después del baneo:
  - **Expulsión permanente** (DM y log)
- Todos los eventos quedan en logs y se publican avisos en los canales correspondientes

---

### ✅ Sistema de Prórrogas de Inactividad
- **Usuarios normales**: Pueden pedir prórroga de hasta 7 días enviando un mensaje en `#👨🔧soporte`
  - El bot concede prórroga automáticamente, borra el mensaje y envía confirmación por DM/canal
- **Admins/Mods**: Pueden dar prórrogas ilimitadas vía comando `/prorroga` en `#💻comandos`
  - Mensaje de confirmación en canal y por DM

---

### ✅ Logs y depuración
- Cada acción clave genera logs visibles para Railway y (cuando aplica) en el canal de logs
- Todos los errores y eventos quedan registrados

---

## 🔧 Comandos slash activos

| Comando        | Quién puede usarlo        | Dónde se usa       | Respuesta                      |
|----------------|--------------------------|--------------------|-------------------------------|
| `/estado`      | Todos los miembros       | #💻comandos        | Estado y faltas personales     |
| `/estadisticas`| Solo admins/mods         | #💻comandos        | Totales, estado general        |
| `/prorroga`    | Solo admins/mods         | #💻comandos        | Da prórroga a miembros         |

---

## 🧠 Aspectos técnicos destacados

- IDs y claves gestionadas solo por variables de entorno
- Toda la lógica (por canal/comando) separada de los textos/avisos (`mensajes/`)
- Todos los canales críticos (normas, comandos, faltas) protegidos: solo el bot publica o responde
- Actualizaciones y mejoras no afectan lo ya funcional gracias al diseño modular
- Panel de faltas y reputación siempre actualizado, sin duplicados ni pérdidas

---

## 🔜 Próximos pasos (expansión)

- Módulo para automatizar soporte avanzado
- Integración con panel web o dashboard de reputación
- Registro ampliado en `#📝logs` y más comandos administrativos
- Automatización avanzada de publicaciones en `#🧵go-viral`

---

*Última actualización: 2025-07-04*
