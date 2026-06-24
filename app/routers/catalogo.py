from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.domain.catalogo.schemas import (
    CategoriaCreate, CategoriaOut,
    TematicaCreate, TematicaOut,
    ServicioProductoCreate, ServicioProductoUpdate, ServicioProductoOut
)
from app.services import catalogo_service

router = APIRouter()


# ── Categorías ────────────────────────────────────────────────────────────────

@router.get("/categorias", response_model=List[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return catalogo_service.listar_categorias(db)


@router.post("/categorias", response_model=CategoriaOut, status_code=201)
def crear_categoria(
    datos: CategoriaCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return catalogo_service.crear_categoria(datos, db)


# ── Temáticas ─────────────────────────────────────────────────────────────────

@router.get("/tematicas", response_model=List[TematicaOut])
def listar_tematicas(categoria_id: int = None, db: Session = Depends(get_db)):
    return catalogo_service.listar_tematicas(categoria_id, db)


@router.post("/tematicas", response_model=TematicaOut, status_code=201)
def crear_tematica(
    datos: TematicaCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return catalogo_service.crear_tematica(datos, db)


# ── Servicios y Productos ─────────────────────────────────────────────────────

@router.get("/servicios", response_model=List[ServicioProductoOut])
def listar_servicios(
    proveedor_id: int = None,
    categoria_id: int = None,
    db: Session = Depends(get_db)
):
    """Lista servicios/productos activos. Filtra por proveedor o categoría."""
    return catalogo_service.listar_servicios(proveedor_id, categoria_id, db)


@router.get("/servicios/{servicio_id}", response_model=ServicioProductoOut)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    return catalogo_service.obtener_servicio(servicio_id, db)


@router.post("/servicios", response_model=ServicioProductoOut, status_code=201)
def crear_servicio(
    datos: ServicioProductoCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return catalogo_service.crear_servicio(datos, db)


@router.patch("/servicios/{servicio_id}", response_model=ServicioProductoOut)
def actualizar_servicio(
    servicio_id: int,
    datos: ServicioProductoUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    return catalogo_service.actualizar_servicio(servicio_id, datos, db)


@router.delete("/servicios/{servicio_id}", status_code=204)
def eliminar_servicio(
    servicio_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Soft delete: guarda la fecha de eliminación sin borrar el registro."""
    catalogo_service.eliminar_servicio(servicio_id, db)