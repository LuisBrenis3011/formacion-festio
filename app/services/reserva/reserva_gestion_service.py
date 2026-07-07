from typing import List
from datetime import datetime, UTC
from fastapi import HTTPException
from app.domain.reservas.models import Reserva, Evento
from app.domain.reservas.schemas import MisReservasItemOut, MisReservasDetalleOut
from app.domain.usuarios.models import Cliente, Proveedor, Usuario
from app.domain.catalogo.models import Paquete, ServicioProducto
from app.domain.common.enums import EstadoReserva
from app.repositories.reserva_repository import ReservaRepository, EventoRepository
from app.repositories.usuario_repository import ClienteRepository, ProveedorRepository
from app.repositories.catalogo_repository import PaqueteRepository, ServicioProductoRepository

def obtener_reserva(reserva_id: int, reserva_repo: ReservaRepository) -> Reserva:
    """Busca una reserva activa por ID. Lanza 404 si no existe o fue eliminada."""
    reserva = reserva_repo.db.query(Reserva).filter(
        Reserva.id == reserva_id,
        Reserva.deleted_at == None
    ).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva


def cancelar_reserva(reserva_id: int, usuario: Usuario, reserva_repo: ReservaRepository) -> dict:
    """Cancela una reserva confirmada (soft delete)."""
    # La ownership real de una reserva se resuelve por la cadena Usuario -> Cliente -> Evento -> Reserva.
    reserva = (
        reserva_repo.db.query(Reserva)
        .join(Evento, Reserva.evento_id == Evento.id)
        .join(Cliente, Evento.cliente_id == Cliente.id)
        .filter(
            Reserva.id == reserva_id,
            Reserva.deleted_at == None,
            Cliente.usuario_id == usuario.id,
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if reserva.estado == EstadoReserva.COMPLETADA:
        raise HTTPException(
            status_code=400, detail="No se puede cancelar una reserva completada"
        )

    reserva.estado = EstadoReserva.CANCELADA
    reserva.deleted_at = datetime.now(UTC)
    reserva_repo.db.commit()
    return {"mensaje": "Reserva cancelada correctamente"}


def listar_mis_reservas(
    usuario: Usuario,
    reserva_repo: ReservaRepository,
    evento_repo: EventoRepository,
    cliente_repo: ClienteRepository,
    proveedor_repo: ProveedorRepository,
    paquete_repo: PaqueteRepository,
    servicio_repo: ServicioProductoRepository,
    skip: int = 0,
    limit: int = 100,
) -> List[MisReservasItemOut]:
    """Devuelve todas las reservas del cliente autenticado, con detalles del evento y proveedor."""
    cliente = cliente_repo.db.query(Cliente).filter(Cliente.usuario_id == usuario.id).first()
    if not cliente:
        return []

    eventos = evento_repo.db.query(Evento).filter(Evento.cliente_id == cliente.id).all()
    evento_ids = [e.id for e in eventos]
    if not evento_ids:
        return []

    reservas = (
        reserva_repo.db.query(Reserva)
        .filter(Reserva.evento_id.in_(evento_ids), Reserva.deleted_at.is_(None))
        .order_by(Reserva.fecha_creacion.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    resultado: List[MisReservasItemOut] = []
    for reserva in reservas:
        evento = next((e for e in eventos if e.id == reserva.evento_id), None)
        if not evento:
            continue

        proveedor = proveedor_repo.db.query(Proveedor).filter(Proveedor.id == reserva.proveedor_id).first()
        nombre_empresa = proveedor.nombre_empresa if proveedor else "Proveedor"

        detalles_out: List[MisReservasDetalleOut] = []
        for det in reserva.detalles:
            if det.deleted_at:
                continue
            if det.paquete_id:
                paq = paquete_repo.db.query(Paquete).filter(Paquete.id == det.paquete_id).first()
                nombre = paq.nombre if paq else f"Paquete #{det.paquete_id}"
                tipo = "paquete"
            else:
                sp = servicio_repo.db.query(ServicioProducto).filter(ServicioProducto.id == det.servicio_producto_id).first()
                nombre = sp.nombre if sp else f"Servicio #{det.servicio_producto_id}"
                tipo = "adicional"
            detalles_out.append(MisReservasDetalleOut(
                nombre=nombre,
                tipo=tipo,
                cantidad=det.cantidad,
                subtotal=float(det.subtotal),
            ))

        resultado.append(MisReservasItemOut(
            reserva_id=reserva.id,
            estado=reserva.estado.value if hasattr(reserva.estado, 'value') else str(reserva.estado),
            nombre_evento=evento.nombre_evento,
            tipo_evento=evento.tipo_evento,
            fecha_evento_inicio=evento.fecha_evento_inicio,
            fecha_evento_fin=evento.fecha_evento_fin,
            direccion=evento.direccion,
            nombre_empresa=nombre_empresa,
            monto_total=float(reserva.monto_total),
            monto_adelanto=float(reserva.monto_adelanto),
            monto_pendiente=float(reserva.monto_pendiente),
            fecha_creacion=reserva.fecha_creacion,
            detalles=detalles_out,
        ))

    return resultado
