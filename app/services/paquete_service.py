from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.catalogo import Paquete, DetallePaquete
from app.models.enums import EstadoBasico
from app.schemas.catalogo import PaqueteCreate, PaqueteUpdate


def listar_paquetes(
    proveedor_id: Optional[int],
    categoria_id: Optional[int],
    tematica_id: Optional[int],
    db: Session,
) -> List[Paquete]:
    """Lista paquetes activos con filtros opcionales."""
    query = db.query(Paquete).filter(Paquete.estado == EstadoBasico.ACTIVO)
    if proveedor_id:
        query = query.filter(Paquete.proveedor_id == proveedor_id)
    if categoria_id:
        query = query.filter(Paquete.categoria_id == categoria_id)
    if tematica_id:
        query = query.filter(Paquete.tematica_id == tematica_id)
    return query.all()


def obtener_paquete(paquete_id: int, db: Session) -> Paquete:
    """Busca un paquete por ID. Lanza 404 si no existe."""
    paquete = db.query(Paquete).filter(Paquete.id == paquete_id).first()
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return paquete


def crear_paquete(datos: PaqueteCreate, db: Session) -> Paquete:
    """Crea un paquete con todos sus detalles en una sola operación."""
    paquete = Paquete(
        proveedor_id=datos.proveedor_id,
        categoria_id=datos.categoria_id,
        tematica_id=datos.tematica_id,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        precio_base=datos.precio_base,
    )
    db.add(paquete)
    db.flush()

    for detalle in datos.detalles:
        db.add(DetallePaquete(
            paquete_id=paquete.id,
            servicio_producto_id=detalle.servicio_producto_id,
            cantidad_incluida=detalle.cantidad_incluida,
        ))

    db.commit()
    db.refresh(paquete)
    return paquete


def actualizar_paquete(
    paquete_id: int, datos: PaqueteUpdate, db: Session
) -> Paquete:
    """Actualiza los campos enviados del paquete. Lanza 404 si no existe."""
    paquete = db.query(Paquete).filter(Paquete.id == paquete_id).first()
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(paquete, campo, valor)

    db.commit()
    db.refresh(paquete)
    return paquete


def eliminar_paquete(paquete_id: int, db: Session) -> None:
    """Soft delete: marca el paquete como INACTIVO."""
    paquete = db.query(Paquete).filter(Paquete.id == paquete_id).first()
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    paquete.estado = EstadoBasico.INACTIVO
    db.commit()
