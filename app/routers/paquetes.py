from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.domain.catalogo.schemas import (
    PaqueteCreate,
    PaqueteUpdate,
    PaqueteOut,
)
from app.repositories.catalogo_repository import (
    PaqueteRepository,
    DetallePaqueteRepository,
    get_paquete_repo,
    get_detalle_paquete_repo
)
from app.services import paquete_service

router = APIRouter()


@router.get("/", response_model=List[PaqueteOut])
def listar_paquetes(
    proveedor_id: Optional[int] = Query(None, description="Filtrar por ID de proveedor"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    repo: PaqueteRepository = Depends(get_paquete_repo)
):
    """Lista paquetes activos. Opcionalmente filtra por proveedor o categoría."""
    return paquete_service.listar_paquetes(proveedor_id, categoria_id, repo)


@router.get("/{paquete_id}", response_model=PaqueteOut)
def obtener_paquete(paquete_id: int, repo: PaqueteRepository = Depends(get_paquete_repo)):
    return paquete_service.obtener_paquete(paquete_id, repo)


@router.post("/", response_model=PaqueteOut, status_code=201)
def crear_paquete(
    datos: PaqueteCreate,
    repo: PaqueteRepository = Depends(get_paquete_repo),
    detalle_repo: DetallePaqueteRepository = Depends(get_detalle_paquete_repo),
    _: int = Depends(get_current_user)
):
    """Crea un paquete y sus detalles relacionados en una sola operación."""
    return paquete_service.crear_paquete(datos, repo, detalle_repo)


@router.patch("/{paquete_id}", response_model=PaqueteOut)
def actualizar_paquete(
    paquete_id: int,
    datos: PaqueteUpdate,
    repo: PaqueteRepository = Depends(get_paquete_repo),
    _: int = Depends(get_current_user)
):
    """Actualiza solo los campos proporcionados de un paquete."""
    return paquete_service.actualizar_paquete(paquete_id, datos, repo)


@router.delete("/{paquete_id}", status_code=204)
def eliminar_paquete(
    paquete_id: int,
    repo: PaqueteRepository = Depends(get_paquete_repo),
    _: int = Depends(get_current_user)
):
    """Soft delete: marca el paquete como INACTIVO."""
    paquete_service.eliminar_paquete(paquete_id, repo)
