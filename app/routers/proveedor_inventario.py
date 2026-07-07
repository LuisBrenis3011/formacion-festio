from typing import List

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_proveedor
from app.domain.usuarios.models import Proveedor
from app.domain.catalogo.schemas import (
    ProveedorServicioCreate,
    ProveedorServicioUpdate,
    ServicioProductoOut,
)
from app.repositories.catalogo_repository import (
    CategoriaRepository,
    ServicioProductoRepository,
    get_categoria_repo,
    get_servicio_producto_repo
)
from app.services import proveedor_inventario_service as inv_service

router = APIRouter()


@router.get("/", response_model=List[ServicioProductoOut])
def listar_inventario(
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)
):
    """Lista todos los servicios/productos (activos e inactivos) del proveedor."""
    return inv_service.listar_inventario(proveedor, repo)


@router.get("/{servicio_id}", response_model=ServicioProductoOut)
def obtener_servicio(
    servicio_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)
):
    """Obtiene un servicio específico del proveedor."""
    return inv_service.obtener_servicio(servicio_id, proveedor, repo)


@router.post("/", response_model=ServicioProductoOut, status_code=201)
def crear_servicio(
    datos: ProveedorServicioCreate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo),
    categoria_repo: CategoriaRepository = Depends(get_categoria_repo)
):
    """Crea un nuevo servicio en el inventario del proveedor."""
    return inv_service.crear_servicio(datos, proveedor, repo, categoria_repo)


@router.patch("/{servicio_id}", response_model=ServicioProductoOut)
def actualizar_servicio(
    servicio_id: int,
    datos: ProveedorServicioUpdate,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)
):
    """Actualiza campos de un servicio del proveedor."""
    return inv_service.actualizar_servicio(servicio_id, datos, proveedor, repo)


@router.delete("/{servicio_id}", status_code=204)
def eliminar_servicio(
    servicio_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)
):
    """Realiza un borrado lógico del servicio del proveedor."""
    inv_service.eliminar_servicio(servicio_id, proveedor, repo)
