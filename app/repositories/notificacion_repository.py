from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.notificaciones.models import Notificacion
from pydantic import BaseModel
from fastapi import Depends
from app.database import get_db

class NotificacionRepository(BaseRepository[Notificacion, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Notificacion, db)

def get_notificacion_repo(db: Session = Depends(get_db)) -> NotificacionRepository: return NotificacionRepository(db)
