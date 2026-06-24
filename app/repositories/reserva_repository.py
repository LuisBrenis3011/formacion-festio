from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.reservas.models import Reserva, Evento, DetalleReserva
from pydantic import BaseModel
from fastapi import Depends
from app.database import get_db

class ReservaRepository(BaseRepository[Reserva, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Reserva, db)

class EventoRepository(BaseRepository[Evento, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Evento, db)

class DetalleReservaRepository(BaseRepository[DetalleReserva, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(DetalleReserva, db)

def get_reserva_repo(db: Session = Depends(get_db)) -> ReservaRepository: return ReservaRepository(db)
def get_evento_repo(db: Session = Depends(get_db)) -> EventoRepository: return EventoRepository(db)
def get_detalle_reserva_repo(db: Session = Depends(get_db)) -> DetalleReservaRepository: return DetalleReservaRepository(db)
