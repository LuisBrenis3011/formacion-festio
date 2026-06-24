from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.personal.models import Personal, PersonalRol
from pydantic import BaseModel
from fastapi import Depends
from app.database import get_db

class PersonalRepository(BaseRepository[Personal, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Personal, db)

class PersonalRolRepository(BaseRepository[PersonalRol, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(PersonalRol, db)

def get_personal_repo(db: Session = Depends(get_db)) -> PersonalRepository: return PersonalRepository(db)
def get_personal_rol_repo(db: Session = Depends(get_db)) -> PersonalRolRepository: return PersonalRolRepository(db)
