# 📁 ESTRUCTURA DEL BOT — Viral 𝕏 | V𝕏

Este archivo documenta la estructura actual del bot, su estado por módulo y su propósito. Se actualiza a medida que el bot crece. Cada módulo está diseñado para ser independiente, escalable y fácil de mantener.

---

## 📂 Archivos raíz

| Archivo        | Estado        | Propósito |
|----------------|---------------|-----------|
| `main.py`      | ✅ Ya trabajado | Arranca el bot, carga cogs y eventos |
| `config.py`    | ✅ Ya trabajado | Contiene los valores globales como IDs y tokens |
| `requirements.txt` | ✅ Ya trabajado | Lista de dependencias para Railway |

---

## 📂 `/mensajes/` — Contenido visual y configuración central

| Archivo                  | Estado        | Propósito |
|--------------------------|---------------|-----------|
| `normas_texto.py`        | ✅ Ya trabajado | Texto completo del mensaje de normas generales |
| `normas_config.py`       | ✅ Ya trabajado | Variables de configuración funcional del bot para las normas |

---

## 📂 `/canales/` — Módulos por canal

| Archivo                  | Estado        | Propósito |
|--------------------------|---------------|-----------|
| `presentate.py`          | ✅ Ya trabajado | Módulo para dar la bienvenida con menú desplegable en `#👋preséntate` |
| `normas_generales.py`    | ✅ Ya trabajado | Limpia y mantiene actualizado `#✅normas-generales` |

---

## 🗂️ Planificación futura

| Módulo                   | Estado        | Propósito previsto |
|--------------------------|---------------|---------------------|
| `faltas.py`              | 🧠 Planificado | Registrar y controlar el sistema de faltas por incumplimiento |
| `go_viral.py`            | 🧠 Planificado | Validar, corregir, y procesar publicaciones en `#🧵go-viral` |
| `logs.py`                | 🧠 Planificado | Registrar toda la actividad del bot en `#📝logs` |
| `soporte.py`             | 🧠 Planificado | Automatizar respuestas y solicitudes en `#👨🔧soporte` |

---

## 🧠 Notas importantes

- Todos los módulos están pensados para ser independientes. Nuevas funciones no deben romper lo ya implementado.
- Las normas generales están divididas en dos partes:
  - Visual (`normas_texto.py`)
  - Configuración funcional (`normas_config.py`)
- El canal `#✅normas-generales` es de uso exclusivo del bot. No se permite texto de usuarios, pero sí reacciones.

---

*Última actualización: 2025-07-02*
