"""
Servicio de Disponibilidad — Validación de inventario en tiempo real.

Verifica dos niveles de capacidad:
1. Por ítem: stock_maximo_simultaneo de cada ServicioProducto
2. Global: capacidad_humana_total del Proveedor (tope físico de personas)

Usa SUM agregado en vez de .first() para manejar múltiples registros
de ocupación solapados en el mismo rango horario.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.domain.catalogo.models       import ServicioProducto
from app.domain.disponibilidad.models import OcupacionServicioProducto, OcupacionGlobalProveedor
from app.domain.common.enums          import EstadoBasico
from app.domain.usuarios.models        import Proveedor
from app.domain.reservas.schemas       import DetalleReservaCreate, DisponibilidadResponse


def consultar_disponibilidad(
    proveedor_id: int,
    fecha_inicio: datetime,
    fecha_fin:    datetime,
    detalles:     List[DetalleReservaCreate],
    db:           Session,
) -> DisponibilidadResponse:
    """
    Verifica si todos los ítems solicitados tienen stock
    disponible en el rango horario del evento.
    """
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        return DisponibilidadResponse(disponible=False, mensaje="Proveedor no encontrado")

    items_no_disponibles: List[str] = []
    personas_requeridas = 0

    for detalle in detalles:
        if not detalle.servicio_producto_id:
            continue

        servicio = db.query(ServicioProducto).filter(
            ServicioProducto.id == detalle.servicio_producto_id,
            ServicioProducto.deleted_at == None,
            ServicioProducto.estado == EstadoBasico.ACTIVO,
        ).first()

        if not servicio:
            items_no_disponibles.append(f"Ítem ID {detalle.servicio_producto_id} no existe o está inactivo")
            continue

        # SUM agregado: maneja múltiples ocupaciones solapadas
        cantidad_ocupada = (
            db.query(func.coalesce(func.sum(OcupacionServicioProducto.cantidad_ocupada), 0))
            .filter(
                OcupacionServicioProducto.servicio_producto_id == servicio.id,
                OcupacionServicioProducto.fecha_hora_inicio < fecha_fin,
                OcupacionServicioProducto.fecha_hora_fin    > fecha_inicio,
            )
            .scalar()
        )

        stock = int(servicio.stock_maximo_simultaneo or 0)
        cantidad_disponible = stock - int(cantidad_ocupada)

        if cantidad_disponible < detalle.cantidad:
            items_no_disponibles.append(
                f"{servicio.nombre}: disponible {cantidad_disponible}, solicitado {detalle.cantidad}"
            )

        # Acumular personas requeridas para validar el tope global del proveedor
        if servicio.requiere_persona:
            personas_requeridas += detalle.cantidad

    # Validar tope físico global del proveedor
    if personas_requeridas > 0:
        ya_ocupadas = (
            db.query(func.coalesce(func.sum(OcupacionGlobalProveedor.total_personas_ocupadas), 0))
            .filter(
                OcupacionGlobalProveedor.proveedor_id      == proveedor_id,
                OcupacionGlobalProveedor.fecha_hora_inicio  < fecha_fin,
                OcupacionGlobalProveedor.fecha_hora_fin     > fecha_inicio,
            )
            .scalar()
        )

        cupo_libre = int(proveedor.capacidad_humana_total or 0) - int(ya_ocupadas)

        if personas_requeridas > cupo_libre:
            items_no_disponibles.append(
                f"Capacidad humana del proveedor: disponible {cupo_libre}, "
                f"solicitado {personas_requeridas}"
            )

    if items_no_disponibles:
        return DisponibilidadResponse(
            disponible=False,
            mensaje="No hay disponibilidad para todos los ítems solicitados",
            items_no_disponibles=items_no_disponibles,
        )

    return DisponibilidadResponse(
        disponible=True,
        mensaje="Todos los ítems están disponibles para el horario solicitado"
    )
