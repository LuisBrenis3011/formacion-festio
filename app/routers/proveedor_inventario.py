from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_proveedor
from app.database import get_db
from app.domain.usuarios.models import Proveedor
from app.domain.catalogo.schemas import (
    ProveedorServicioCreate, ProveedorServicioUpdate, ServicioProductoOut,
)
from app.services import proveedor_inventario_service as inv_service

router = APIRouter()


@router.get("/", response_model=List[ServicioProductoOut])
def listar_inventario(
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Lista todos los servicios/productos del proveedor logueado."""
    return inv_service.listar_inventario(proveedor, db)


@router.get("/{servicio_id}", response_model=ServicioProductoOut)
def obtener_servicio(
    servicio_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Detalle de un servicio propio."""
    return inv_service.obtener_servicio(servicio_id, proveedor, db)


@router.post("/", response_model=ServicioProductoOut, status_code=201)
def crear_servicio(
    datos: ProveedorServicioCreate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Crea un nuevo servicio/producto en el inventario del proveedor."""
    return inv_service.crear_servicio(datos, proveedor, db)


@router.patch("/{servicio_id}", response_model=ServicioProductoOut)
def actualizar_servicio(
    servicio_id: int,
    datos: ProveedorServicioUpdate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Actualiza un servicio propio."""
    return inv_service.actualizar_servicio(servicio_id, datos, proveedor, db)


@router.delete("/{servicio_id}", status_code=204)
def eliminar_servicio(
    servicio_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    db: Session = Depends(get_db),
):
    """Soft-delete de un servicio propio."""
    inv_service.eliminar_servicio(servicio_id, proveedor, db)
