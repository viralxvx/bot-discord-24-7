# 📘 DOCUMENTACIÓN TÉCNICA — VXbot

Este documento resume las funcionalidades ya implementadas en el bot **VXbot**, la infraestructura utilizada, su arquitectura modular y las automatizaciones activas hasta el momento.

---

## 🚀 Infraestructura y tecnologías

- **Lenguaje**: Python 3.10+
- **Librería principal**: `discord.py v2.3.2`
- **Base de datos**: Redis (`redis==5.0.1`)
- **Deploy**: Railway (pago)
- **Gestión de secretos**: Variables de entorno en Railway
- **Estructura**: Modular, organizada por carpetas (`canales/`, `comandos/`, `mensajes/`)
- **Estado persistente**: Redis + opcionalmente JSON

---

## 🧩 Funciones implementadas

### ✅ Canal `#👋preséntate`
- Envía mensaje de bienvenida visualmente profesional
- Incluye menú desplegable con enlaces a:
  - 📖 `#guías`
  - ✅ `#normas-generales`
  - 🏆 `#victorias`
  - ♟ `#estrategias-probadas`
  - 🏋 `#entrenamiento`
- Totalmente automático al iniciar

---

### ✅ Canal `#✅normas-generales`
- Limpia todos los mensajes (incluyendo fijados)
- Publica las normas divididas en **dos embeds elegantes**
- Si ya existen, los edita sin duplicar
- Si un usuario escribe algo, el bot borra el mensaje
- Soporta actualizaciones centralizadas desde `mensajes/`

---

### ✅ Canal `#📤faltas` (panel público)
- Un mensaje por miembro (no se duplica)
- Se edita automáticamente si cambia el estado
- Si el usuario es expulsado, se elimina
- Contenido:
  - Foto de perfil como avatar
  - 📤 `REGISTRO DE @usuario`
  - Estado actual
  - Total de faltas
  - Faltas del mes
  - Footer con fecha elegante (ej. "ayer a las 21:10")
- Se sincroniza al iniciar el bot

---

### ✅ Canal `#💻comandos`
- Canal exclusivo para ejecutar comandos
- Limpia mensajes antiguos al iniciar
- Muestra instrucciones de uso:
  - `/estado`: muestra tus faltas actuales y estado (accesible a todos)
  - `/estadisticas`: muestra estadísticas generales del servidor (solo admins)
- Las respuestas:
  - Se publican en el canal por **10 minutos**
  - Se envían también por DM

---

## 🔧 Comandos slash activos

| Comando        | Quién puede usarlo | Respuesta |
|----------------|--------------------|-----------|
| `/estado`      | Todos los miembros | Muestra cantidad de faltas, estado y advertencias |
| `/estadisticas`| Solo admins        | Muestra totales: miembros, baneados, expulsados |

---

## 🧠 Aspectos técnicos destacados

- Todas las IDs se gestionan por variables de entorno
- Uso completo de `discord.app_commands` para comandos slash
- Separación clara entre lógica (`canales/`, `comandos/`) y contenido (`mensajes/`)
- Uso de `await canal.history()` sin `.flatten()`, ya que Discord.py 2.x no lo necesita
- Limpieza y sincronización eficiente del canal de faltas: edita si existe, crea si no

---

## 🔜 Próximos pasos (pendientes)

- Sistema automático de baneo y expulsiones por inactividad
- Módulo para `#🧵go-viral` con verificación de formato y faltas
- Registro de actividad en `#📝logs`
- Módulo de soporte automático

---

*Última actualización: 2025-07-02*
