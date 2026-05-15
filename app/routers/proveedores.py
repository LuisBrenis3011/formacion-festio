from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.usuario import ProveedorCreate, ProveedorUpdate, ProveedorOut
from app.services import proveedor_service

router = APIRouter()


@router.get("/", response_model=List[ProveedorOut])
def listar_proveedores(
    distrito: str = None,
    db: Session = Depends(get_db)
):
    """Lista todos los proveedores verificados. Filtra por distrito si se indica."""
    return proveedor_service.listar_proveedores(distrito, db)


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def obtener_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    return proveedor_service.obtener_proveedor(proveedor_id, db)


@router.post("/", response_model=ProveedorOut, status_code=201)
def crear_proveedor(
    datos: ProveedorCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return proveedor_service.crear_proveedor(datos, db)


@router.patch("/{proveedor_id}", response_model=ProveedorOut)
def actualizar_proveedor(
    proveedor_id: int,
    datos: ProveedorUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return proveedor_service.actualizar_proveedor(proveedor_id, datos, db)