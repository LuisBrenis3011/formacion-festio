from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.catalogo.models import Categoria, Tematica, ServicioProducto, Paquete, DetallePaquete
from pydantic import BaseModel
from fastapi import Depends
from app.database import get_db

class CategoriaRepository(BaseRepository[Categoria, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Categoria, db)

class TematicaRepository(BaseRepository[Tematica, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Tematica, db)

class ServicioProductoRepository(BaseRepository[ServicioProducto, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(ServicioProducto, db)

class PaqueteRepository(BaseRepository[Paquete, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(Paquete, db)

class DetallePaqueteRepository(BaseRepository[DetallePaquete, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(DetallePaquete, db)

class DetallePaqueteRepository(BaseRepository[DetallePaquete, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(DetallePaquete, db)

def get_categoria_repo(db: Session = Depends(get_db)) -> CategoriaRepository: return CategoriaRepository(db)
def get_tematica_repo(db: Session = Depends(get_db)) -> TematicaRepository: return TematicaRepository(db)
def get_servicio_producto_repo(db: Session = Depends(get_db)) -> ServicioProductoRepository: return ServicioProductoRepository(db)
def get_paquete_repo(db: Session = Depends(get_db)) -> PaqueteRepository: return PaqueteRepository(db)
def get_detalle_paquete_repo(db: Session = Depends(get_db)) -> DetallePaqueteRepository: return DetallePaqueteRepository(db)
