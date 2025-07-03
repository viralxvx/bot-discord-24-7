# 📁 ESTRUCTURA DEL BOT — Viral 𝕏 | V𝕏

Este archivo documenta la estructura **real y actual** del bot, el estado de cada módulo y su propósito. Actualizado con los módulos de inactividad, soporte y prórroga. El diseño es modular, seguro y escalable.

---

## 📂 Archivos raíz

| Archivo             | Estado         | Propósito                                         |
|---------------------|----------------|---------------------------------------------------|
| `main.py`           | ✅ Ya trabajado | Arranca el bot, carga cogs y mantiene vivo en Railway |
| `config.py`         | ✅ Ya trabajado | Centraliza todas las variables de entorno         |
| `requirements.txt`  | ✅ Ya trabajado | Lista de dependencias para Railway                |

---

## 📂 `/mensajes/` — Contenido visual y configuración central

| Archivo                  | Estado         | Propósito                                               |
|--------------------------|----------------|---------------------------------------------------------|
| `normas_texto.py`        | ✅ Ya trabajado | Texto completo de normas generales (editables)          |
| `normas_config.py`       | ✅ Ya trabajado | Configuración funcional para normas                     |
| `comandos_texto.py`      | ✅ Ya trabajado | Instrucciones y embeds del canal de comandos            |
| `inactividad_texto.py`   | ✅ Ya trabajado | Mensajes de baneo, expulsión y prórroga (editables)     |

---

## 📂 `/canales/` — Módulos por canal

| Archivo                  | Estado         | Propósito                                                      |
|--------------------------|----------------|----------------------------------------------------------------|
| `presentate.py`          | ✅ Ya trabajado | Bienvenida automática en `#👋preséntate` con menú interactivo   |
| `normas_generales.py`    | ✅ Ya trabajado | Limpia y mantiene el mensaje fijo de normas                    |
| `faltas.py`              | ✅ Ya trabajado | Genera y sincroniza el panel público en `#📤faltas`            |
| `comandos.py`            | ✅ Ya trabajado | Limpia y configura instrucciones en `#💻comandos`               |
| `inactividad.py`         | ✅ Ya trabajado | Detecta inactividad, ejecuta baneos y expulsiones automáticas  |
| `soporte_prorroga.py`    | ✅ Ya trabajado | Gestiona solicitudes de prórroga de usuarios en `#👨🔧soporte`   |

---

## 📂 `/comandos/` — Comandos slash

| Archivo                  | Estado         | Propósito                                                      |
|--------------------------|----------------|----------------------------------------------------------------|
| `estado.py`              | ✅ Ya trabajado | Consulta de faltas y estado individual                         |
| `estadisticas.py`        | ✅ Ya trabajado | Estadísticas globales del servidor para admins/mods            |
| `prorroga.py`            | ✅ Ya trabajado | Comando para que admins/mods den prórrogas a cualquier usuario |

---

## 🗂️ Planificación futura

| Módulo                   | Estado         | Propósito previsto                                 |
|--------------------------|----------------|----------------------------------------------------|
| `go_viral.py`            | 🧠 Planificado  | Automatizar validación y corrección en `#🧵go-viral`|
| `logs.py`                | 🧠 Planificado  | Registrar eventos y auditoría en `#📝logs`          |
| `soporte.py`             | 🧠 Planificado  | Mejorar atención automática y FAQ en soporte        |

---

## 🧠 Notas importantes

- Todos los módulos son **independientes**. Fallos en uno no afectan a los demás.
- El bot es completamente **modular y seguro** para añadir funciones.
- Canales críticos (`#comandos`, `#faltas`, `#normas-generales`) están protegidos: solo el bot publica.
- El panel de faltas y los comandos slash **se sincronizan automáticamente** al iniciar el bot.
- Los mensajes y textos que ve el usuario están **centralizados en `/mensajes/`** para fácil edición sin tocar código.
- Sistema de **inactividad y prórrogas** 100% automático, sin intervención humana, configurable y seguro.

---

*Última actualización: 2025-07-04*
