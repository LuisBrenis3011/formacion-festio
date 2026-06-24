from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.domain.disponibilidad.models import OcupacionServicioProducto, OcupacionGlobalProveedor
from pydantic import BaseModel
from fastapi import Depends
from app.database import get_db

class OcupacionServicioProductoRepository(BaseRepository[OcupacionServicioProducto, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(OcupacionServicioProducto, db)

class OcupacionGlobalProveedorRepository(BaseRepository[OcupacionGlobalProveedor, BaseModel, BaseModel]):
    def __init__(self, db: Session):
        super().__init__(OcupacionGlobalProveedor, db)

def get_ocupacion_servicio_producto_repo(db: Session = Depends(get_db)) -> OcupacionServicioProductoRepository: return OcupacionServicioProductoRepository(db)
def get_ocupacion_global_proveedor_repo(db: Session = Depends(get_db)) -> OcupacionGlobalProveedorRepository: return OcupacionGlobalProveedorRepository(db)
