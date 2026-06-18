"""
Lógica de negocio para el inventario del proveedor autenticado.
Reutiliza el modelo ServicioProducto pero con scope al proveedor logueado.
"""
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.catalogo import Categoria, ServicioProducto
from app.models.enums import EstadoBasico
from app.models.usuario import Proveedor
from app.schemas.catalogo import ProveedorServicioCreate, ProveedorServicioUpdate


def listar_inventario(proveedor: Proveedor, db: Session) -> List[ServicioProducto]:
    """Lista todos los servicios/productos del proveedor (activos y no eliminados)."""
    return (
        db.query(ServicioProducto)
        .filter(
            ServicioProducto.proveedor_id == proveedor.id,
            ServicioProducto.deleted_at == None,
        )
        .order_by(ServicioProducto.id.desc())
        .all()
    )


def obtener_servicio(servicio_id: int, proveedor: Proveedor, db: Session) -> ServicioProducto:
    """Busca un servicio que pertenezca al proveedor. Lanza 404 si no es suyo."""
    servicio = db.query(ServicioProducto).filter(
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
    db: Session,
) -> ServicioProducto:
    """Crea un servicio/producto para el proveedor logueado."""
    # Validar que la categoría existe
    categoria = db.query(Categoria).filter(Categoria.id == datos.categoria_id).first()
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
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


def actualizar_servicio(
    servicio_id: int,
    datos: ProveedorServicioUpdate,
    proveedor: Proveedor,
    db: Session,
) -> ServicioProducto:
    """Actualiza un servicio que pertenezca al proveedor logueado."""
    servicio = obtener_servicio(servicio_id, proveedor, db)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(servicio, campo, valor)

    db.commit()
    db.refresh(servicio)
    return servicio


def eliminar_servicio(servicio_id: int, proveedor: Proveedor, db: Session) -> None:
    """Soft delete: guarda la fecha de eliminación."""
    servicio = obtener_servicio(servicio_id, proveedor, db)
    servicio.deleted_at = datetime.utcnow()
    db.commit()
