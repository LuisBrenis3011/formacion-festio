from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_proveedor
from app.database import get_db
from app.models.usuario import Proveedor
from app.schemas.catalogo import (
    ProveedorPaqueteCreate, ProveedorPaqueteUpdate, PaqueteOut,
)
from app.services import proveedor_paquete_service as paq_service

router = APIRouter()


@router.get("/", response_model=List[PaqueteOut])
def listar_paquetes(
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Lista todos los paquetes activos del proveedor logueado."""
    return paq_service.listar_paquetes(proveedor, db)


@router.get("/{paquete_id}", response_model=PaqueteOut)
def obtener_paquete(
    paquete_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Detalle de un paquete propio."""
    return paq_service.obtener_paquete(paquete_id, proveedor, db)


@router.post("/", response_model=PaqueteOut, status_code=201)
def crear_paquete(
    datos: ProveedorPaqueteCreate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Crea un paquete armando la composición con servicios propios."""
    return paq_service.crear_paquete(datos, proveedor, db)


@router.patch("/{paquete_id}", response_model=PaqueteOut)
def actualizar_paquete(
    paquete_id: int,
    datos: ProveedorPaqueteUpdate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Actualiza un paquete propio. Puede reemplazar detalles."""
    return paq_service.actualizar_paquete(paquete_id, datos, proveedor, db)


@router.delete("/{paquete_id}", status_code=204)
def eliminar_paquete(
    paquete_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Soft-delete de un paquete propio."""
    paq_service.eliminar_paquete(paquete_id, proveedor, db)
