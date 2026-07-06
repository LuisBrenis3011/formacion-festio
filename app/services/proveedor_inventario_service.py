"""
Lógica de negocio para el inventario del proveedor autenticado.
Reutiliza el modelo ServicioProducto pero con scope al proveedor logueado.
"""
from datetime import datetime, UTC
from typing import List

from fastapi import HTTPException

from app.domain.catalogo.models import ServicioProducto
from app.domain.usuarios.models import Proveedor
from app.domain.catalogo.schemas import ProveedorServicioCreate, ProveedorServicioUpdate

from app.repositories.catalogo_repository import CategoriaRepository, ServicioProductoRepository


def listar_inventario(proveedor: Proveedor, repo: ServicioProductoRepository) -> List[ServicioProducto]:
    """Lista todos los servicios/productos del proveedor (activos y no eliminados)."""
    return (
        repo.db.query(ServicioProducto)
        .filter(
            ServicioProducto.proveedor_id == proveedor.id,
            ServicioProducto.deleted_at == None,
        )
        .order_by(ServicioProducto.id.desc())
        .all()
    )


def obtener_servicio(servicio_id: int, proveedor: Proveedor, repo: ServicioProductoRepository) -> ServicioProducto:
    """Busca un servicio que pertenezca al proveedor. Lanza 404 si no es suyo."""
    servicio = repo.db.query(ServicioProducto).filter(
        ServicioProducto.id == servicio_id,
        ServicioProducto.proveedor_id == proveedor.id,
        ServicioProducto.deleted_at == None,
    ).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado en tu inventario")
    return servicio


def crear_servicio(
    datos: ProveedorServicioCreate,
    proveedor: Proveedor,
    repo: ServicioProductoRepository,
    categoria_repo: CategoriaRepository,
) -> ServicioProducto:
    """Crea un servicio/producto para el proveedor logueado."""
    # Validar que la categoría existe
    categoria = categoria_repo.get(datos.categoria_id)
    if not categoria:
        raise HTTPException(status_code=400, detail="Categoría no encontrada")

    servicio = ServicioProducto(
        proveedor_id=proveedor.id,
        categoria_id=datos.categoria_id,
        nombre=datos.nombre,
        tipo=datos.tipo,
        requiere_persona=datos.requiere_persona,
        precio_unitario=datos.precio_unitario,
        stock_maximo_simultaneo=datos.stock_maximo_simultaneo,
        duracion_base_horas=datos.duracion_base_horas,
    )
    repo.db.add(servicio)
    repo.db.commit()
    repo.db.refresh(servicio)
    return servicio


def actualizar_servicio(
    servicio_id: int,
    datos: ProveedorServicioUpdate,
    proveedor: Proveedor,
    repo: ServicioProductoRepository,
) -> ServicioProducto:
    """Actualiza un servicio que pertenezca al proveedor logueado."""
    servicio = obtener_servicio(servicio_id, proveedor, repo)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(servicio, campo, valor)

    repo.db.commit()
    repo.db.refresh(servicio)
    return servicio


def eliminar_servicio(servicio_id: int, proveedor: Proveedor, repo: ServicioProductoRepository) -> None:
    """Soft delete: guarda la fecha de eliminación."""
    servicio = obtener_servicio(servicio_id, proveedor, repo)
    servicio.deleted_at = datetime.now(UTC)
    repo.db.commit()
