from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.resenas.models import Resena
from pydantic import BaseModel
from fastapi import Depends
from app.database import get_db

class ResenaRepository(BaseRepository[Resena, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Resena, db)

def get_resena_repo(db: Session = Depends(get_db)) -> ResenaRepository: return ResenaRepository(db)
