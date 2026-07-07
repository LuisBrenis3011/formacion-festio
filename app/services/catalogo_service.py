from datetime import datetime, UTC
from typing import List, Optional

from fastapi import HTTPException

from app.domain.catalogo.models import Categoria, Tematica, ServicioProducto
from app.domain.common.enums import EstadoBasico
from app.domain.catalogo.schemas import (
    CategoriaCreate,
    TematicaCreate,
    ServicioProductoCreate,
    ServicioProductoUpdate,
)
from app.repositories.catalogo_repository import CategoriaRepository, TematicaRepository, ServicioProductoRepository


# ── Categorías ────────────────────────────────────────────────────────────────

def listar_categorias(repo: CategoriaRepository) -> List[Categoria]:
    """Retorna todas las categorías."""
    return repo.get_all()


def crear_categoria(datos: CategoriaCreate, repo: CategoriaRepository) -> Categoria:
    """Crea una nueva categoría."""
    return repo.create(datos)


# ── Temáticas ─────────────────────────────────────────────────────────────────

def listar_tematicas(categoria_id: Optional[int], repo: TematicaRepository) -> List[Tematica]:
    """Lista temáticas. Filtra por categoría si se indica."""
    query = repo.db.query(Tematica)
    if categoria_id:
        query = query.filter(Tematica.categoria_id == categoria_id)
    return query.all()


def crear_tematica(datos: TematicaCreate, repo: TematicaRepository) -> Tematica:
    """Crea una nueva temática."""
    return repo.create(datos)


# ── Servicios y Productos ─────────────────────────────────────────────────────

def listar_servicios(
    proveedor_id: Optional[int],
    categoria_id: Optional[int],
    repo: ServicioProductoRepository,
) -> List[ServicioProducto]:
    """Lista servicios/productos activos. Filtra por proveedor o categoría."""
    query = repo.db.query(ServicioProducto).filter(
        ServicioProducto.estado == EstadoBasico.ACTIVO,
        ServicioProducto.deleted_at == None
    )
    if proveedor_id:
        query = query.filter(ServicioProducto.proveedor_id == proveedor_id)
    if categoria_id:
        query = query.filter(ServicioProducto.categoria_id == categoria_id)
    return query.all()


def obtener_servicio(servicio_id: int, repo: ServicioProductoRepository) -> ServicioProducto:
    """Busca un servicio por ID. Lanza 404 si no existe o fue eliminado."""
    servicio = repo.db.query(ServicioProducto).filter(
        ServicioProducto.id == servicio_id,
        ServicioProducto.deleted_at == None
    ).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio


def crear_servicio(datos: ServicioProductoCreate, repo: ServicioProductoRepository) -> ServicioProducto:
    """Crea un nuevo servicio/producto."""
    return repo.create(datos)


def actualizar_servicio(
    servicio_id: int, datos: ServicioProductoUpdate, repo: ServicioProductoRepository
) -> ServicioProducto:
    """Actualiza los campos enviados del servicio. Lanza 404 si no existe."""
    servicio = repo.update(servicio_id, datos)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio


def eliminar_servicio(servicio_id: int, repo: ServicioProductoRepository) -> None:
    """Soft delete: guarda la fecha de eliminación sin borrar el registro."""
    servicio = repo.get(servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    servicio.deleted_at = datetime.now(UTC)
    repo.db.commit()
