import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Configuración del bot
TOKEN = os.environ["TOKEN"]
CANAL_OBJETIVO = os.environ["CANAL_OBJETIVO"]
CANAL_LOGS = "📝logs"
CANAL_REPORTES = "⛔reporte-de-incumplimiento"
CANAL_SOPORTE = "👨🔧soporte"
CANAL_FLUJO_SOPORTE = "flujo-de-soporte"
CANAL_ANUNCIOS = "🔔anuncios"
CANAL_NORMAS_GENERALES = "✅normas-generales"
CANAL_X_NORMAS = "𝕏-normas"
CANAL_FALTAS = "📤faltas"
ADMIN_ID = os.environ.get("ADMIN_ID", "1174775323649392844")
INACTIVITY_TIMEOUT = 300  # 5 minutos en segundos
MAX_MENSAJES_RECIENTES = 10
MAX_LOG_LENGTH = 1900
SAVE_STATE_DELAY = 5
last_save_time = 0

# Configuración de la base de datos PostgreSQL
if "DATABASE_URL" not in os.environ:
    raise Exception("Error: La variable de entorno DATABASE_URL no está configurada. Configúrala en Railway.")
DATABASE_URL = os.environ["DATABASE_URL"]
if not DATABASE_URL.startswith("postgresql+psycopg2://"):
    if DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://").replace("postgresql://", "postgresql+psycopg2://")
    if "?sslmode" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    connect_args={'connect_timeout': 10}
)
Base = declarative_base()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
