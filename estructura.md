# 📁 ESTRUCTURA DEL BOT — Viral 𝕏 | V𝕏

Este archivo documenta la estructura actual del bot, su estado por módulo y su propósito. Se actualiza a medida que el bot crece. Cada módulo está diseñado para ser independiente, escalable y fácil de mantener.

---

## 📂 Archivos raíz

| Archivo             | Estado         | Propósito |
|---------------------|----------------|-----------|
| `main.py`           | ✅ Ya trabajado | Arranca el bot, carga cogs y mantiene vivo en Railway |
| `config.py`         | ✅ Ya trabajado | Centraliza todas las variables de entorno |
| `requirements.txt`  | ✅ Ya trabajado | Lista de dependencias para Railway |

---

## 📂 `/mensajes/` — Contenido visual y configuración central

| Archivo                  | Estado         | Propósito |
|--------------------------|----------------|-----------|
| `normas_texto.py`        | ✅ Ya trabajado | Texto completo del mensaje de normas generales |
| `normas_config.py`       | ✅ Ya trabajado | Variables de configuración funcional del bot para normas |
| `comandos_texto.py`      | ✅ Ya trabajado | Instrucciones y embeds del canal de comandos |

---

## 📂 `/canales/` — Módulos por canal

| Archivo                  | Estado         | Propósito |
|--------------------------|----------------|-----------|
| `presentate.py`          | ✅ Ya trabajado | Bienvenida automática en `#👋preséntate` con menú |
| `normas_generales.py`    | ✅ Ya trabajado | Limpia y mantiene el mensaje fijo de normas |
| `faltas.py`              | ✅ Ya trabajado | Genera y sincroniza el panel público en `#📤faltas` |
| `comandos.py`            | ✅ Ya trabajado | Limpia y configura instrucciones en `#💻comandos` |

---

## 📂 `/comandos/` — Comandos slash

| Archivo                  | Estado         | Propósito |
|--------------------------|----------------|-----------|
| `estado.py`              | ✅ Ya trabajado | Muestra el estado individual del usuario |
| `estadisticas.py`        | ✅ Ya trabajado | Muestra estadísticas globales para admins |

---

## 🗂️ Planificación futura

| Módulo                   | Estado         | Propósito previsto |
|--------------------------|----------------|---------------------|
| `go_viral.py`            | 🧠 Planificado  | Automatizar validación en `#🧵go-viral` |
| `logs.py`                | 🧠 Planificado  | Registrar eventos en `#📝logs` |
| `soporte.py`             | 🧠 Planificado  | Gestionar asistencia automática |

---

## 🧠 Notas importantes

- Todos los módulos son independientes. Fallos en uno no afectan al resto.
- El bot es completamente modular y seguro para escalar.
- El canal de comandos es exclusivo y debe usarse solo para `/estado` y `/estadisticas`.
- El canal de faltas se sincroniza al iniciar, sin duplicar.

---

*Última actualización: 2025-07-02*
