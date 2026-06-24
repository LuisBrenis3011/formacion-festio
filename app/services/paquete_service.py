from typing import List, Optional

from fastapi import HTTPException

from app.domain.catalogo.models import Paquete, DetallePaquete
from app.domain.common.enums import EstadoBasico
from app.domain.catalogo.schemas import PaqueteCreate, PaqueteUpdate
from app.repositories.catalogo_repository import PaqueteRepository, DetallePaqueteRepository


def listar_paquetes(
    proveedor_id: Optional[int],
    categoria_id: Optional[int],
    repo: PaqueteRepository,
) -> List[Paquete]:
    """Lista paquetes activos con filtros opcionales."""
    query = repo.db.query(Paquete).filter(Paquete.estado == EstadoBasico.ACTIVO)
    if proveedor_id:
        query = query.filter(Paquete.proveedor_id == proveedor_id)
    if categoria_id:
        query = query.filter(Paquete.categoria_id == categoria_id)
    return query.all()


def obtener_paquete(paquete_id: int, repo: PaqueteRepository) -> Paquete:
    """Busca un paquete por ID. Lanza 404 si no existe."""
    paquete = repo.get(paquete_id)
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return paquete


def crear_paquete(datos: PaqueteCreate, repo: PaqueteRepository, detalle_repo: DetallePaqueteRepository) -> Paquete:
    """Crea un paquete con todos sus detalles en una sola operación."""
    paquete = Paquete(
        proveedor_id=datos.proveedor_id,
        categoria_id=datos.categoria_id,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        precio_base=datos.precio_base,
    )
    repo.db.add(paquete)
    repo.db.flush()

    for detalle in datos.detalles:
        detalle_repo.db.add(DetallePaquete(
            paquete_id=paquete.id,
            servicio_producto_id=detalle.servicio_producto_id,
            cantidad_incluida=detalle.cantidad_incluida,
        ))

    repo.db.commit()
    repo.db.refresh(paquete)
    return paquete


def actualizar_paquete(
    paquete_id: int, datos: PaqueteUpdate, repo: PaqueteRepository
) -> Paquete:
    """Actualiza los campos enviados del paquete. Lanza 404 si no existe."""
    paquete = repo.update(paquete_id, datos)
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return paquete


def eliminar_paquete(paquete_id: int, repo: PaqueteRepository) -> None:
    """Soft delete: marca el paquete como INACTIVO."""
    paquete = repo.get(paquete_id)
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    paquete.estado = EstadoBasico.INACTIVO
    repo.db.commit()
