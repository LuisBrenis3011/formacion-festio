"""
Lógica de negocio para los paquetes del proveedor autenticado.
Valida ownership de servicios al armar un paquete.
"""
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.domain.catalogo.models import (
    Categoria, DetallePaquete, Paquete, ServicioProducto, Tematica,
)
from app.domain.common.enums import EstadoBasico
from app.domain.usuarios.models import Proveedor
from app.domain.catalogo.schemas import ProveedorPaqueteCreate, ProveedorPaqueteUpdate


def listar_paquetes(proveedor: Proveedor, db: Session) -> List[Paquete]:
    """Lista paquetes del proveedor con detalles cargados."""
    return (
        db.query(Paquete)
        .options(
            joinedload(Paquete.detalles).joinedload(DetallePaquete.servicio_producto),
        )
        .filter(
            Paquete.proveedor_id == proveedor.id,
            Paquete.estado == EstadoBasico.ACTIVO,
        )
        .order_by(Paquete.id.desc())
        .all()
    )


def obtener_paquete(paquete_id: int, proveedor: Proveedor, db: Session) -> Paquete:
    """Busca un paquete que pertenezca al proveedor. Lanza 404 si no es suyo."""
    paquete = (
        db.query(Paquete)
        .options(
            joinedload(Paquete.detalles).joinedload(DetallePaquete.servicio_producto),
        )
        .filter(
            Paquete.id == paquete_id,
            Paquete.proveedor_id == proveedor.id,
        )
        .first()
    )
    if not paquete:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return paquete


def crear_paquete(
    datos: ProveedorPaqueteCreate,
    proveedor: Proveedor,
    db: Session,
) -> Paquete:
    """Crea un paquete con detalles. Valida ownership de cada servicio incluido."""
    # Validar categoría
    categoria = db.query(Categoria).filter(Categoria.id == datos.categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=400, detail="Categoría no encontrada")

    # Validar temática (si se provee)
    if datos.tematica_id:
        tematica = db.query(Tematica).filter(
            Tematica.id == datos.tematica_id,
            Tematica.categoria_id == datos.categoria_id,
        ).first()
        if not tematica:
            raise HTTPException(
                status_code=400,
                detail="Temática no encontrada o no pertenece a la categoría seleccionada",
            )

    # Validar que TODOS los servicios en detalles pertenezcan al proveedor
    if not datos.detalles:
        raise HTTPException(status_code=400, detail="El paquete debe incluir al menos un servicio")

    srv_ids = [d.servicio_producto_id for d in datos.detalles]
    servicios_propios = (
        db.query(ServicioProducto.id)
        .filter(
            ServicioProducto.id.in_(srv_ids),
            ServicioProducto.proveedor_id == proveedor.id,
            ServicioProducto.deleted_at == None,
        )
        .all()
    )
    ids_validos = {s.id for s in servicios_propios}
    ids_invalidos = set(srv_ids) - ids_validos
    if ids_invalidos:
        raise HTTPException(
            status_code=400,
            detail=f"Los siguientes servicios no están en tu inventario: {ids_invalidos}",
        )

    paquete = Paquete(
        proveedor_id=proveedor.id,
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
    # Re-cargar con joins
    return obtener_paquete(paquete.id, proveedor, db)


def actualizar_paquete(
    paquete_id: int,
    datos: ProveedorPaqueteUpdate,
    proveedor: Proveedor,
    db: Session,
) -> Paquete:
    """Actualiza campos del paquete y opcionalmente reemplaza sus detalles."""
    paquete = obtener_paquete(paquete_id, proveedor, db)

    # Actualizar campos simples
    campos_simples = datos.model_dump(exclude_unset=True, exclude={"detalles"})
    for campo, valor in campos_simples.items():
        setattr(paquete, campo, valor)

    # Si envían detalles, reemplazar la composición completa
    if datos.detalles is not None:
        if not datos.detalles:
            raise HTTPException(status_code=400, detail="El paquete debe incluir al menos un servicio")

        # Validar ownership de los nuevos servicios
        srv_ids = [d.servicio_producto_id for d in datos.detalles]
        servicios_propios = (
            db.query(ServicioProducto.id)
            .filter(
                ServicioProducto.id.in_(srv_ids),
                ServicioProducto.proveedor_id == proveedor.id,
                ServicioProducto.deleted_at == None,
            )
            .all()
        )
        ids_validos = {s.id for s in servicios_propios}
        ids_invalidos = set(srv_ids) - ids_validos
        if ids_invalidos:
            raise HTTPException(
                status_code=400,
                detail=f"Servicios no válidos: {ids_invalidos}",
            )

        # Borrar detalles viejos y crear nuevos
        db.query(DetallePaquete).filter(DetallePaquete.paquete_id == paquete.id).delete()
        for detalle in datos.detalles:
            db.add(DetallePaquete(
                paquete_id=paquete.id,
                servicio_producto_id=detalle.servicio_producto_id,
                cantidad_incluida=detalle.cantidad_incluida,
            ))

    db.commit()
    return obtener_paquete(paquete.id, proveedor, db)


def eliminar_paquete(paquete_id: int, proveedor: Proveedor, db: Session) -> None:
    """Soft delete: marca el paquete como INACTIVO."""
    paquete = obtener_paquete(paquete_id, proveedor, db)
    paquete.estado = EstadoBasico.INACTIVO
    db.commit()
