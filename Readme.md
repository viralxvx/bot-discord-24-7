# Bot de Discord para Comunidad VX

## Estructura del Proyecto
.
├── .gitignore
├── Dockerfile
├── Procfile
├── README.md
├── requirements.txt
├── main.py                     # Punto de entrada principal
├── config.py                   # Configuración del bot
├── redis_database.py           # Conexión y gestión de Redis
├── discord_bot.py              # Instancia principal del bot
├── state_management.py         # Gestión del estado con Redis
├── utils.py                    # Utilidades comunes
├── commands/                   # Comandos con prefijo !
│   └── permisos.py             # Comando !permiso
├── events/                     # Manejadores de eventos
│   ├── on_member.py            # Eventos de entrada/salida de miembros
│   ├── on_message.py           # Manejo de mensajes en canales
│   └── on_ready.py             # Evento al iniciar el bot
├── handlers/                   # Manejadores específicos por canal
│   ├── anuncios.py             # #🔔anuncios
│   ├── faltas.py               # #📤faltas
│   ├── go_viral.py             # #🧵go-viral (principal)
│   ├── normas_generales.py     # #✅normas-generales
│   ├── reporte_incumplimiento.py # #⛔reporte-de-incumplimiento
│   ├── soporte.py              # #👨🔧soporte
│   └── x_normas.py             # #𝕏-normas
├── tasks/                      # Tareas programadas
│   ├── __init__.py             # Para paquete Python
│   ├── clean_inactive.py       # Limpiar conversaciones inactivas
│   ├── limpiar_expulsados.py   # Limpiar mensajes de expulsados
│   ├── reset_faltas.py         # Resetear faltas diarias
│   └── verificar_inactividad.py # Verificar inactividad
└── views/                      # Componentes de UI interactiva
    ├── __init__.py             # Exporta vistas principales
    ├── report_menu.py          # Menú de reportes
    └── support_menu.py         # Menú de soporte
