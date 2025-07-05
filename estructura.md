---

# 📁 ESTRUCTURA DEL BOT — Viral 𝕏 | V𝕏

Este archivo documenta la estructura **real y actual** del bot, el estado de cada módulo y su propósito. Incluye automatización avanzada y funciones adaptativas. El diseño es modular, seguro, escalable y permite configuración integral desde Discord.

---

## 📂 Archivos raíz

| Archivo            | Estado         | Propósito                                             |
| ------------------ | -------------- | ----------------------------------------------------- |
| `main.py`          | ✅ Ya trabajado | Arranca el bot, carga cogs y mantiene vivo en Railway |
| `config.py`        | ✅ Ya trabajado | Centraliza todas las variables de entorno             |
| `requirements.txt` | ✅ Ya trabajado | Lista de dependencias para Railway                    |

---

## 📂 `/mensajes/` — Contenido visual y configuración central

| Archivo                | Estado         | Propósito                                             |
| ---------------------- | -------------- | ----------------------------------------------------- |
| `normas_texto.py`      | ✅ Ya trabajado | Texto completo de normas generales (editables)        |
| `normas_config.py`     | ✅ Ya trabajado | Configuración funcional para normas                   |
| `comandos_texto.py`    | ✅ Ya trabajado | Instrucciones y embeds del canal de comandos          |
| `inactividad_texto.py` | ✅ Ya trabajado | Mensajes de baneo, expulsión y prórroga (editables)   |
| `viral_texto.py`       | ✅ Ya trabajado | Todos los embeds, notificaciones y textos de go-viral |

---

## 📂 `/canales/` — Módulos por canal

| Archivo                     | Estado         | Propósito                                                                                                                                   |
| --------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `presentate.py`             | ✅ Ya trabajado | Bienvenida automática en `#👋preséntate` con menú interactivo                                                                               |
| `normas_generales.py`       | ✅ Ya trabajado | Limpia y mantiene el mensaje fijo de normas                                                                                                 |
| `faltas.py`                 | ✅ Ya trabajado | Genera y sincroniza el panel público en `#📤faltas`                                                                                         |
| `comandos.py`               | ✅ Ya trabajado | Limpia y configura instrucciones en `#💻comandos`                                                                                           |
| `inactividad.py`            | ✅ Ya trabajado | Detecta inactividad, ejecuta baneos y expulsiones automáticas                                                                               |
| `soporte_prorroga.py`       | ✅ Ya trabajado | Gestiona solicitudes de prórroga de usuarios en `#👨🔧soporte`                                                                              |
| `go_viral.py`               | ✅ Ya trabajado | **Automatiza todo en `#🧵go-viral`: reglas, control, embeds, validaciones, override, sincronización total de reacciones y apoyos en Redis** |
| `configuraciones.py`        | 🧠 Planificado | **Permite a admins/mods modificar y recargar cualquier parámetro/configuración del bot desde Discord**                                      |
| `nuevas_funciones.py`       | 🧠 Planificado | Publica automáticamente toda actualización, nueva función, fix, versión o canal creado en `#🚀nuevas-funciones`                             |
| `anuncios.py`               | 🧠 Planificado | Anuncia en `#📣anuncios` los cambios de normas generales y lleva al usuario a las normas sombreadas                                         |
| `reporte_incumplimiento.py` | 🧠 Planificado | Permite a usuarios reportar falta de apoyo (🔥) en X, envía avisos, advertencias, notifica a quien reporta y a quien es reportado           |

---

## 📂 `/comandos/` — Comandos slash

| Archivo           | Estado         | Propósito                                                                            |
| ----------------- | -------------- | ------------------------------------------------------------------------------------ |
| `estado.py`       | ✅ Ya trabajado | Consulta de faltas y estado individual                                               |
| `estadisticas.py` | ✅ Ya trabajado | Estadísticas globales del servidor para admins/mods                                  |
| `prorroga.py`     | ✅ Ya trabajado | Comando para que admins/mods den prórrogas a cualquier usuario                       |
| `override.py`     | ✅ Ya trabajado | Permite publicar en go-viral a un usuario aunque no cumpla reglas (emergencia/admin) |
| `config.py`       | 🧠 Planificado | **Comando global para modificar/apagar/encender cualquier función/config del bot**   |
| `reporte.py`      | 🧠 Planificado | Permite a usuarios reportar incumplimientos directamente                             |

---

## 🗂️ Planificación futura

| Módulo               | Estado         | Propósito previsto                                                                                 |
| -------------------- | -------------- | -------------------------------------------------------------------------------------------------- |
| `logs.py`            | 🧠 Planificado | Registrar eventos y auditoría en `#📝logs`                                                         |
| `soporte.py`         | 🧠 Planificado | Mejorar atención automática y FAQ en soporte                                                       |
| `configuraciones.py` | 🧠 Planificado | Panel/configuración avanzada: apagar/encender sistemas, límites, reglas, todo editable por Discord |

---

## 🧠 Notas importantes

* Todos los módulos son **independientes**. Fallos en uno no afectan a los demás.
* El bot es completamente **modular y seguro** para añadir funciones nuevas sin romper nada.
* Canales críticos (`#comandos`, `#faltas`, `#normas-generales`, `#go-viral`) están protegidos: solo el bot publica.
* El panel de faltas y los comandos slash **se sincronizan automáticamente** al iniciar el bot.
* Los mensajes y textos que ve el usuario están **centralizados en `/mensajes/`** para fácil edición sin tocar código.
* Sistemas de **inactividad, faltas, go-viral, prórrogas y reporte de incumplimientos** 100% automáticos, seguros y auditables.
* Todos los embeds y mensajes públicos son profesionales, educativos y pueden editarse en caliente.
* El bot registra el **historial completo del canal** `#🧵go-viral` en Redis para evitar confusiones de usuarios nuevos o antiguos tras reinicio.
* **Las reglas de reacciones, apoyos, intervalos y overrides se aplican siempre** — incluso a mensajes anteriores al reinicio gracias a la limpieza/sincronización de reacciones y apoyos en Redis.
* El sistema de configuración avanzada permitirá:

  * Apagar/encender el bot o módulos desde Discord
  * Modificar cualquier parámetro en caliente (apoyo, intervalos, faltas, permisos…)
  * Al editar las normas generales, TODO el sistema se actualiza y sincroniza en todos los canales relevantes, incluyendo anuncios y resaltar cambios para los usuarios.
  * Automatización de reportes, gestión y notificaciones a usuarios y admins.

---

*Última actualización: 2025-07-05 — 00:42am*

---

