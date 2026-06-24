from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.usuarios.models import Usuario, Cliente, Proveedor
from pydantic import BaseModel

class UsuarioRepository(BaseRepository[Usuario, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Usuario, db)
        
    def get_by_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(self.model).filter(self.model.email == email).first()

class ClienteRepository(BaseRepository[Cliente, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Cliente, db)

class ProveedorRepository(BaseRepository[Proveedor, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Proveedor, db)

from fastapi import Depends
from app.database import get_db

def get_usuario_repo(db: Session = Depends(get_db)) -> UsuarioRepository:
    return UsuarioRepository(db)

def get_cliente_repo(db: Session = Depends(get_db)) -> ClienteRepository:
    return ClienteRepository(db)

def get_proveedor_repo(db: Session = Depends(get_db)) -> ProveedorRepository:
    return ProveedorRepository(db)
