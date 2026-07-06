from typing import List
from datetime import datetime
from fastapi import HTTPException
from app.domain.reservas.models import Reserva, Evento
from app.domain.reservas.schemas import MisReservasItemOut, MisReservasDetalleOut
from app.domain.usuarios.models import Cliente, Proveedor, Usuario
from app.domain.catalogo.models import Paquete, ServicioProducto
from app.domain.common.enums import EstadoReserva
from app.repositories.reserva_repository import ReservaRepository, EventoRepository
from app.repositories.usuario_repository import ClienteRepository, ProveedorRepository
from app.repositories.catalogo_repository import PaqueteRepository, ServicioProductoRepository

from app.domain.common.enums import EstadoPago, MetodoPago, TipoPago
from app.domain.pagos.models import PagoTransaccion
from app.domain.reservas.schemas import CompletarReservaRequest, CompletarReservaResponse
from app.repositories.pago_repository import PagoTransaccionRepository

from app.domain.reservas.schemas import ProveedorReservaItemOut
from app.repositories.usuario_repository import UsuarioRepository

def obtener_reserva(reserva_id: int, reserva_repo: ReservaRepository) -> Reserva:
    """Busca una reserva activa por ID. Lanza 404 si no existe o fue eliminada."""
    reserva = reserva_repo.db.query(Reserva).filter(
        Reserva.id == reserva_id,
        Reserva.deleted_at == None
    ).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva


def cancelar_reserva(reserva_id: int, reserva_repo: ReservaRepository) -> dict:
    """Cancela una reserva confirmada (soft delete)."""
    reserva = reserva_repo.db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if reserva.estado == EstadoReserva.COMPLETADA:
        raise HTTPException(
            status_code=400, detail="No se puede cancelar una reserva completada"
        )

    reserva.estado = EstadoReserva.CANCELADA
    reserva.deleted_at = datetime.utcnow()
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

def completar_reserva(
    reserva_id: int,
    datos: CompletarReservaRequest,
    proveedor: Proveedor,
    reserva_repo: ReservaRepository,
    pago_repo: PagoTransaccionRepository,
) -> CompletarReservaResponse:
    """
    Marca una reserva CONFIRMADA como COMPLETADA y registra el pago
    del saldo pendiente (90%) cobrado presencialmente por el proveedor.
    """
    reserva = (
        reserva_repo.db.query(Reserva)
        .filter(
            Reserva.id == reserva_id,
            Reserva.proveedor_id == proveedor.id,
            Reserva.deleted_at.is_(None),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if reserva.estado != EstadoReserva.CONFIRMADA:
        raise HTTPException(
            status_code=400,
            detail=f"Solo se puede completar una reserva CONFIRMADA (estado actual: {reserva.estado.value}).",
        )

    if reserva.monto_pendiente <= 0:
        raise HTTPException(status_code=400, detail="Esta reserva no tiene saldo pendiente por cobrar.")

    pago = PagoTransaccion(
        reserva_id=reserva.id,
        tipo_pago=TipoPago.SALDO_PRESENCIAL,
        monto=reserva.monto_pendiente,
        metodo_pago=datos.metodo_pago,
        estado=EstadoPago.APROBADO,
        codigo_transaccion=datos.codigo_transaccion,
    )
    pago_repo.db.add(pago)

    monto_pagado = float(reserva.monto_pendiente)
    reserva.monto_pendiente = 0
    reserva.estado = EstadoReserva.COMPLETADA

    pago_repo.db.commit()
    pago_repo.db.refresh(pago)

    return CompletarReservaResponse(
        reserva_id=reserva.id,
        estado=reserva.estado.value,
        pago_id=pago.id,
        monto_pagado=monto_pagado,
        mensaje="Reserva marcada como completada y saldo registrado correctamente.",
    )


def listar_reservas_proveedor(
    proveedor: Proveedor,
    reserva_repo: ReservaRepository,
    evento_repo: EventoRepository,
    cliente_repo: ClienteRepository,
    usuario_repo: UsuarioRepository,
    paquete_repo: PaqueteRepository,
    servicio_repo: ServicioProductoRepository,
) -> List[ProveedorReservaItemOut]:
    """Devuelve todas las reservas del proveedor autenticado, con datos del cliente."""
    reservas = (
        reserva_repo.db.query(Reserva)
        .filter(Reserva.proveedor_id == proveedor.id, Reserva.deleted_at.is_(None))
        .order_by(Reserva.fecha_creacion.desc())
        .all()
    )

    resultado: List[ProveedorReservaItemOut] = []
    for reserva in reservas:
        evento = evento_repo.db.query(Evento).filter(Evento.id == reserva.evento_id).first()
        if not evento:
            continue

        nombre_cliente = "Cliente"
        cliente = cliente_repo.db.query(Cliente).filter(Cliente.id == evento.cliente_id).first()
        if cliente:
            usuario_cliente = usuario_repo.db.query(Usuario).filter(Usuario.id == cliente.usuario_id).first()
            if usuario_cliente:
                nombre_cliente = f"{usuario_cliente.nombre} {usuario_cliente.apellido}"

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
                nombre=nombre, tipo=tipo, cantidad=det.cantidad, subtotal=float(det.subtotal),
            ))

        resultado.append(ProveedorReservaItemOut(
            reserva_id=reserva.id,
            estado=reserva.estado.value if hasattr(reserva.estado, "value") else str(reserva.estado),
            nombre_evento=evento.nombre_evento,
            tipo_evento=evento.tipo_evento,
            fecha_evento_inicio=evento.fecha_evento_inicio,
            fecha_evento_fin=evento.fecha_evento_fin,
            direccion=evento.direccion,
            nombre_cliente=nombre_cliente,
            monto_total=float(reserva.monto_total),
            monto_adelanto=float(reserva.monto_adelanto),
            monto_pendiente=float(reserva.monto_pendiente),
            fecha_creacion=reserva.fecha_creacion,
            detalles=detalles_out,
        ))

    return resultado