from sqlalchemy import Column, String, Integer, JSON, DateTime
from .config import Base

class State(Base):
    __tablename__ = "bot_state"
    id = Column(String, primary_key=True)
    ultima_publicacion_dict = Column(JSON)
    amonestaciones = Column(JSON)
    baneos_temporales = Column(JSON)
    permisos_inactividad = Column(JSON)
    ticket_counter = Column(Integer, default=0)
    active_conversations = Column(JSON)
    faq_data = Column(JSON)
    faltas_dict = Column(JSON)
    mensajes_recientes = Column(JSON)
