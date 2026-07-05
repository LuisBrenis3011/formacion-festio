from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import require_role
from app.domain.common.enums import RolUsuario
from app.domain.catalogo.schemas import (
    CategoriaCreate,
    CategoriaOut,
    TematicaCreate,
    TematicaOut,
    ServicioProductoCreate,
    ServicioProductoUpdate,
    ServicioProductoOut,
)
from app.repositories.catalogo_repository import (
    CategoriaRepository,
    TematicaRepository,
    ServicioProductoRepository,
    get_categoria_repo,
    get_tematica_repo,
    get_servicio_producto_repo
)
from app.services import catalogo_service

router = APIRouter()


# ── Categorías ────────────────────────────────────────────────────────────────

@router.get("/categorias", response_model=List[CategoriaOut])
def listar_categorias(repo: CategoriaRepository = Depends(get_categoria_repo)):
    return catalogo_service.listar_categorias(repo)


@router.post("/categorias", response_model=CategoriaOut, status_code=201)
def crear_categoria(
    datos: CategoriaCreate,
    repo: CategoriaRepository = Depends(get_categoria_repo),
    _: object = Depends(require_role(RolUsuario.PROVEEDOR))
):
    return catalogo_service.crear_categoria(datos, repo)


# ── Temáticas ─────────────────────────────────────────────────────────────────

@router.get("/tematicas", response_model=List[TematicaOut])
def listar_tematicas(
    categoria_id: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    repo: TematicaRepository = Depends(get_tematica_repo)
):
    return catalogo_service.listar_tematicas(categoria_id, repo)


@router.post("/tematicas", response_model=TematicaOut, status_code=201)
def crear_tematica(
    datos: TematicaCreate,
    repo: TematicaRepository = Depends(get_tematica_repo),
    _: object = Depends(require_role(RolUsuario.PROVEEDOR))
):
    return catalogo_service.crear_tematica(datos, repo)


# ── Servicios y Productos ─────────────────────────────────────────────────────

@router.get("/servicios", response_model=List[ServicioProductoOut])
def listar_servicios(
    proveedor_id: Optional[int] = Query(None, description="Filtrar por ID de proveedor"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)
):
    """Lista servicios/productos activos. Filtra por proveedor o categoría."""
    return catalogo_service.listar_servicios(proveedor_id, categoria_id, repo)


@router.get("/servicios/{servicio_id}", response_model=ServicioProductoOut)
def obtener_servicio(servicio_id: int, repo: ServicioProductoRepository = Depends(get_servicio_producto_repo)):
    return catalogo_service.obtener_servicio(servicio_id, repo)


@router.post("/servicios", response_model=ServicioProductoOut, status_code=201)
def crear_servicio(
    datos: ServicioProductoCreate,
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo),
    _: object = Depends(require_role(RolUsuario.PROVEEDOR))
):
    return catalogo_service.crear_servicio(datos, repo)


@router.patch("/servicios/{servicio_id}", response_model=ServicioProductoOut)
def actualizar_servicio(
    servicio_id: int,
    datos: ServicioProductoUpdate,
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo),
    _: object = Depends(require_role(RolUsuario.PROVEEDOR))
):
    return catalogo_service.actualizar_servicio(servicio_id, datos, repo)


@router.delete("/servicios/{servicio_id}", status_code=204)
def eliminar_servicio(
    servicio_id: int,
    repo: ServicioProductoRepository = Depends(get_servicio_producto_repo),
    _: object = Depends(require_role(RolUsuario.PROVEEDOR))
):
    """Soft delete: guarda la fecha de eliminación sin borrar el registro."""
    catalogo_service.eliminar_servicio(servicio_id, repo)
