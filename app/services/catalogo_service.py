from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.catalogo.models import Categoria, Tematica, ServicioProducto
from app.domain.common.enums import EstadoBasico
from app.domain.catalogo.schemas import (
    CategoriaCreate,
    TematicaCreate,
    ServicioProductoCreate,
    ServicioProductoUpdate,
)


# ── Categorías ────────────────────────────────────────────────────────────────

def listar_categorias(db: Session) -> List[Categoria]:
    """Retorna todas las categorías."""
    return db.query(Categoria).all()


def crear_categoria(datos: CategoriaCreate, db: Session) -> Categoria:
    """Crea una nueva categoría."""
    categoria = Categoria(**datos.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


# ── Temáticas ─────────────────────────────────────────────────────────────────

def listar_tematicas(categoria_id: Optional[int], db: Session) -> List[Tematica]:
    """Lista temáticas. Filtra por categoría si se indica."""
    query = db.query(Tematica)
    if categoria_id:
        query = query.filter(Tematica.categoria_id == categoria_id)
    return query.all()


def crear_tematica(datos: TematicaCreate, db: Session) -> Tematica:
    """Crea una nueva temática."""
    tematica = Tematica(**datos.model_dump())
    db.add(tematica)
    db.commit()
    db.refresh(tematica)
    return tematica


# ── Servicios y Productos ─────────────────────────────────────────────────────

def listar_servicios(
    proveedor_id: Optional[int],
    categoria_id: Optional[int],
    db: Session,
) -> List[ServicioProducto]:
    """Lista servicios/productos activos. Filtra por proveedor o categoría."""
    query = db.query(ServicioProducto).filter(
        ServicioProducto.estado == EstadoBasico.ACTIVO,
        ServicioProducto.deleted_at == None
    )
    if proveedor_id:
        query = query.filter(ServicioProducto.proveedor_id == proveedor_id)
    if categoria_id:
        query = query.filter(ServicioProducto.categoria_id == categoria_id)
    return query.all()


def obtener_servicio(servicio_id: int, db: Session) -> ServicioProducto:
    """Busca un servicio por ID. Lanza 404 si no existe o fue eliminado."""
    servicio = db.query(ServicioProducto).filter(
        ServicioProducto.id == servicio_id,
        ServicioProducto.deleted_at == None
    ).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio


def crear_servicio(datos: ServicioProductoCreate, db: Session) -> ServicioProducto:
    """Crea un nuevo servicio/producto."""
    servicio = ServicioProducto(**datos.model_dump())
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


def actualizar_servicio(
    servicio_id: int, datos: ServicioProductoUpdate, db: Session
) -> ServicioProducto:
    """Actualiza los campos enviados del servicio. Lanza 404 si no existe."""
    servicio = db.query(ServicioProducto).filter(
        ServicioProducto.id == servicio_id
    ).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(servicio, campo, valor)

    db.commit()
    db.refresh(servicio)
    return servicio


def eliminar_servicio(servicio_id: int, db: Session) -> None:
    """Soft delete: guarda la fecha de eliminación sin borrar el registro."""
    servicio = db.query(ServicioProducto).filter(
        ServicioProducto.id == servicio_id
    ).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    servicio.deleted_at = datetime.utcnow()
    db.commit()
