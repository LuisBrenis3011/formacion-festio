from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_proveedor
from app.domain.usuarios.models import Proveedor
from app.domain.catalogo.schemas import (
    ProveedorPaqueteCreate,
    ProveedorPaqueteUpdate,
    PaqueteOut,
)
from app.repositories.catalogo_repository import (
    PaqueteRepository,
    DetallePaqueteRepository,
    CategoriaRepository,
    TematicaRepository,
    ServicioProductoRepository,
    get_paquete_repo,
    get_detalle_paquete_repo,
    get_categoria_repo,
    get_tematica_repo,
    get_servicio_producto_repo
)
from app.services import proveedor_paquete_service as paq_service

router = APIRouter()


@router.get("/", response_model=List[PaqueteOut])
def listar_paquetes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PaqueteRepository = Depends(get_paquete_repo),
):
    return paq_service.listar_paquetes(proveedor, repo, skip=skip, limit=limit)


@router.get("/{paquete_id}", response_model=PaqueteOut)
def obtener_paquete(
    paquete_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PaqueteRepository = Depends(get_paquete_repo)
):
    """Detalle de un paquete propio."""
    return paq_service.obtener_paquete(paquete_id, proveedor, repo)


@router.post("/", response_model=PaqueteOut, status_code=201)
def crear_paquete(
    datos: ProveedorPaqueteCreate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PaqueteRepository = Depends(get_paquete_repo),
    detalle_repo: DetallePaqueteRepository = Depends(get_detalle_paquete_repo),
    categoria_repo: CategoriaRepository = Depends(get_categoria_repo),
    tematica_repo: TematicaRepository = Depends(get_tematica_repo),
    servicio_repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)
):
    """Crea un nuevo paquete combinando servicios propios del proveedor."""
    return paq_service.crear_paquete(
        datos, proveedor, repo, detalle_repo, categoria_repo, tematica_repo, servicio_repo
    )


@router.patch("/{paquete_id}", response_model=PaqueteOut)
def actualizar_paquete(
    paquete_id: int,
    datos: ProveedorPaqueteUpdate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PaqueteRepository = Depends(get_paquete_repo),
    detalle_repo: DetallePaqueteRepository = Depends(get_detalle_paquete_repo),
    servicio_repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)
):
    """Actualiza campos simples o la composición del paquete."""
    return paq_service.actualizar_paquete(
        paquete_id, datos, proveedor, repo, detalle_repo, servicio_repo
    )


@router.delete("/{paquete_id}", status_code=204)
def eliminar_paquete(
    paquete_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: PaqueteRepository = Depends(get_paquete_repo)
):
    """Realiza un soft-delete de un paquete propio."""
    paq_service.eliminar_paquete(paquete_id, proveedor, repo)
