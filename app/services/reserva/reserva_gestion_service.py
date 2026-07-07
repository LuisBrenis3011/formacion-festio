from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from fastapi import HTTPException

from app.domain.catalogo.models import DetallePaquete, Paquete, ServicioProducto
from app.domain.common.enums import EstadoPago, EstadoReserva, TipoPago
from app.domain.disponibilidad.models import (
    OcupacionGlobalProveedor,
    OcupacionServicioProducto,
)
from app.domain.reservas.models import Reserva, Evento
from app.domain.reservas.schemas import MisReservasItemOut, MisReservasDetalleOut
from app.domain.usuarios.models import Cliente, Proveedor, Usuario
from app.repositories.reserva_repository import ReservaRepository, EventoRepository
from app.repositories.usuario_repository import ClienteRepository, ProveedorRepository
from app.repositories.catalogo_repository import PaqueteRepository, ServicioProductoRepository

from typing import Optional
from app.domain.common.enums import EstadoPago, MetodoPago, TipoPago
from app.domain.pagos.models import PagoTransaccion
from app.repositories.pago_repository import PagoTransaccionRepository

_MONTO_CENTAVOS = Decimal("0.01")

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
    """Cancela una reserva confirmada sin borrar su historial."""
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

    try:
        _validar_reserva_cancelable(reserva)
        _validar_ventana_cancelacion(reserva.evento)
        _validar_pagos_para_cancelacion(reserva)
        servicios_a_liberar, personas_a_liberar = _construir_huella_liberacion(
            reserva, reserva_repo
        )

        for (servicio_producto_id, fecha_inicio, fecha_fin), cantidad in servicios_a_liberar.items():
            _liberar_ocupacion_servicio_exacta(
                reserva_repo,
                servicio_producto_id,
                fecha_inicio,
                fecha_fin,
                cantidad,
            )

        for (proveedor_id, fecha_inicio, fecha_fin), cantidad in personas_a_liberar.items():
            _liberar_ocupacion_global_exacta(
                reserva_repo,
                proveedor_id,
                fecha_inicio,
                fecha_fin,
                cantidad,
            )

        reserva.monto_pendiente = Decimal("0.00")
        reserva.monto_total = _normalizar_monto(reserva.monto_adelanto)
        reserva.estado = EstadoReserva.CANCELADA
        reserva_repo.db.commit()
    except HTTPException:
        reserva_repo.db.rollback()
        raise
    except Exception:
        reserva_repo.db.rollback()
        raise

    return {"mensaje": "Reserva cancelada correctamente"}


def _validar_reserva_cancelable(reserva: Reserva) -> None:
    if reserva.estado == EstadoReserva.COMPLETADA:
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar una reserva completada",
        )

    if reserva.estado == EstadoReserva.CANCELADA:
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar una reserva ya cancelada",
        )

    if reserva.estado != EstadoReserva.CONFIRMADA:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden cancelar reservas confirmadas",
        )


def _validar_ventana_cancelacion(evento: Evento, horas_minimas: int = 48) -> None:
    if not evento or not evento.fecha_evento_inicio:
        raise HTTPException(
            status_code=409,
            detail="La reserva no tiene una fecha de evento valida para cancelar",
        )

    fecha_inicio = evento.fecha_evento_inicio
    ahora = datetime.now(fecha_inicio.tzinfo) if fecha_inicio.tzinfo else datetime.now()
    if fecha_inicio - ahora < timedelta(hours=horas_minimas):
        raise HTTPException(
            status_code=400,
            detail=f"La reserva solo puede cancelarse con al menos {horas_minimas} horas de anticipacion",
        )


def _validar_pagos_para_cancelacion(reserva: Reserva) -> None:
    pagos_aprobados = [
        pago for pago in reserva.pagos if pago.estado == EstadoPago.APROBADO
    ]
    monto_adelanto = _normalizar_monto(reserva.monto_adelanto)

    if monto_adelanto == Decimal("0.00"):
        if pagos_aprobados:
            raise HTTPException(
                status_code=400,
                detail="La reserva tiene pagos aprobados incompatibles con la cancelacion",
            )
        return

    if len(pagos_aprobados) != 1:
        raise HTTPException(
            status_code=400,
            detail="La reserva tiene pagos aprobados incompatibles con la cancelacion",
        )

    pago = pagos_aprobados[0]
    if (
        pago.tipo_pago != TipoPago.ADELANTO_ONLINE
        or _normalizar_monto(pago.monto) != monto_adelanto
    ):
        raise HTTPException(
            status_code=400,
            detail="La reserva tiene pagos aprobados incompatibles con la cancelacion",
        )


def _construir_huella_liberacion(
    reserva: Reserva,
    reserva_repo: ReservaRepository,
) -> tuple[
    Dict[Tuple[int, datetime, datetime], int],
    Dict[Tuple[int, datetime, datetime], int],
]:
    detalles_activos = [detalle for detalle in reserva.detalles if detalle.deleted_at is None]
    if not detalles_activos:
        raise HTTPException(
            status_code=409,
            detail="La reserva no tiene detalles activos suficientes para cancelar de forma segura",
        )

    subtotal_detalles = sum((_normalizar_monto(detalle.subtotal) for detalle in detalles_activos), Decimal("0.00"))
    if subtotal_detalles != _normalizar_monto(reserva.monto_total):
        raise HTTPException(
            status_code=409,
            detail="La reserva no puede cancelarse porque su huella actual es inconsistente con la BD",
        )

    servicios_a_liberar: Dict[Tuple[int, datetime, datetime], int] = {}
    personas_a_liberar: Dict[Tuple[int, datetime, datetime], int] = {}
    servicios_cache: Dict[int, ServicioProducto] = {}
    paquetes_cache: Dict[int, Paquete] = {}
    detalles_paquete_cache: Dict[int, List[DetallePaquete]] = {}

    for detalle in detalles_activos:
        if not detalle.fecha_hora_inicio_servicio or not detalle.fecha_hora_fin_servicio:
            raise HTTPException(
                status_code=409,
                detail="La reserva no puede cancelarse porque tiene detalles sin rango horario",
            )

        if detalle.servicio_producto_id:
            servicio = _obtener_servicio_para_cancelacion(
                detalle.servicio_producto_id,
                reserva.proveedor_id,
                servicios_cache,
                reserva_repo,
            )
            _acumular_servicio(
                servicios_a_liberar,
                detalle.servicio_producto_id,
                detalle.fecha_hora_inicio_servicio,
                detalle.fecha_hora_fin_servicio,
                int(detalle.cantidad or 0),
            )
            if servicio.requiere_persona:
                _acumular_personas(
                    personas_a_liberar,
                    reserva.proveedor_id,
                    detalle.fecha_hora_inicio_servicio,
                    detalle.fecha_hora_fin_servicio,
                    int(detalle.cantidad or 0),
                )
            continue

        if detalle.paquete_id:
            paquete = _obtener_paquete_para_cancelacion(
                detalle.paquete_id,
                reserva.proveedor_id,
                paquetes_cache,
                reserva_repo,
            )
            detalles_paquete = _obtener_detalles_paquete_actuales(
                paquete.id,
                detalles_paquete_cache,
                reserva_repo,
            )
            for detalle_paquete in detalles_paquete:
                servicio = _obtener_servicio_para_cancelacion(
                    detalle_paquete.servicio_producto_id,
                    reserva.proveedor_id,
                    servicios_cache,
                    reserva_repo,
                )
                cantidad_liberada = int(detalle.cantidad or 0) * int(detalle_paquete.cantidad_incluida or 0)
                _acumular_servicio(
                    servicios_a_liberar,
                    detalle_paquete.servicio_producto_id,
                    detalle.fecha_hora_inicio_servicio,
                    detalle.fecha_hora_fin_servicio,
                    cantidad_liberada,
                )
                if servicio.requiere_persona:
                    _acumular_personas(
                        personas_a_liberar,
                        reserva.proveedor_id,
                        detalle.fecha_hora_inicio_servicio,
                        detalle.fecha_hora_fin_servicio,
                        cantidad_liberada,
                    )
            continue

        raise HTTPException(
            status_code=409,
            detail="La reserva no puede cancelarse porque tiene detalles inconsistentes",
        )

    return servicios_a_liberar, personas_a_liberar


def _obtener_servicio_para_cancelacion(
    servicio_producto_id: int,
    proveedor_id: int,
    servicios_cache: Dict[int, ServicioProducto],
    reserva_repo: ReservaRepository,
) -> ServicioProducto:
    servicio = servicios_cache.get(servicio_producto_id)
    if servicio:
        return servicio

    servicio = reserva_repo.db.query(ServicioProducto).filter(
        ServicioProducto.id == servicio_producto_id
    ).first()
    if not servicio or servicio.proveedor_id != proveedor_id:
        raise HTTPException(
            status_code=409,
            detail="La reserva no puede cancelarse porque referencia servicios inconsistentes",
        )

    servicios_cache[servicio_producto_id] = servicio
    return servicio


def _obtener_paquete_para_cancelacion(
    paquete_id: int,
    proveedor_id: int,
    paquetes_cache: Dict[int, Paquete],
    reserva_repo: ReservaRepository,
) -> Paquete:
    paquete = paquetes_cache.get(paquete_id)
    if paquete:
        return paquete

    paquete = reserva_repo.db.query(Paquete).filter(Paquete.id == paquete_id).first()
    if not paquete or paquete.proveedor_id != proveedor_id:
        raise HTTPException(
            status_code=409,
            detail="La reserva no puede cancelarse porque referencia paquetes inconsistentes",
        )

    paquetes_cache[paquete_id] = paquete
    return paquete


def _obtener_detalles_paquete_actuales(
    paquete_id: int,
    detalles_paquete_cache: Dict[int, List[DetallePaquete]],
    reserva_repo: ReservaRepository,
) -> List[DetallePaquete]:
    detalles_paquete = detalles_paquete_cache.get(paquete_id)
    if detalles_paquete is not None:
        return detalles_paquete

    detalles_paquete = reserva_repo.db.query(DetallePaquete).filter(
        DetallePaquete.paquete_id == paquete_id
    ).all()
    if not detalles_paquete:
        raise HTTPException(
            status_code=409,
            detail="La reserva no puede cancelarse porque su paquete ya no tiene composicion disponible",
        )

    detalles_paquete_cache[paquete_id] = detalles_paquete
    return detalles_paquete


def _acumular_servicio(
    servicios_a_liberar: Dict[Tuple[int, datetime, datetime], int],
    servicio_producto_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    cantidad: int,
) -> None:
    if cantidad <= 0:
        raise HTTPException(
            status_code=409,
            detail="La reserva no puede cancelarse porque tiene cantidades inconsistentes",
        )
    clave = (servicio_producto_id, fecha_inicio, fecha_fin)
    servicios_a_liberar[clave] = servicios_a_liberar.get(clave, 0) + cantidad


def _acumular_personas(
    personas_a_liberar: Dict[Tuple[int, datetime, datetime], int],
    proveedor_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    cantidad: int,
) -> None:
    if cantidad <= 0:
        raise HTTPException(
            status_code=409,
            detail="La reserva no puede cancelarse porque tiene cantidades inconsistentes",
        )
    clave = (proveedor_id, fecha_inicio, fecha_fin)
    personas_a_liberar[clave] = personas_a_liberar.get(clave, 0) + cantidad


def _liberar_ocupacion_servicio_exacta(
    reserva_repo: ReservaRepository,
    servicio_producto_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    cantidad: int,
) -> None:
    ocupaciones = reserva_repo.db.query(OcupacionServicioProducto).filter(
        OcupacionServicioProducto.servicio_producto_id == servicio_producto_id,
        OcupacionServicioProducto.fecha_hora_inicio == fecha_inicio,
        OcupacionServicioProducto.fecha_hora_fin == fecha_fin,
    ).order_by(OcupacionServicioProducto.id.asc()).all()

    _decrementar_ocupaciones(
        reserva_repo,
        ocupaciones,
        cantidad,
        lambda ocupacion: int(ocupacion.cantidad_ocupada or 0),
        lambda ocupacion, nuevo_total: setattr(ocupacion, "cantidad_ocupada", nuevo_total),
        "La reserva no puede cancelarse porque la ocupacion del servicio es inconsistente",
    )


def _liberar_ocupacion_global_exacta(
    reserva_repo: ReservaRepository,
    proveedor_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    cantidad: int,
) -> None:
    ocupaciones = reserva_repo.db.query(OcupacionGlobalProveedor).filter(
        OcupacionGlobalProveedor.proveedor_id == proveedor_id,
        OcupacionGlobalProveedor.fecha_hora_inicio == fecha_inicio,
        OcupacionGlobalProveedor.fecha_hora_fin == fecha_fin,
    ).order_by(OcupacionGlobalProveedor.id.asc()).all()

    _decrementar_ocupaciones(
        reserva_repo,
        ocupaciones,
        cantidad,
        lambda ocupacion: int(ocupacion.total_personas_ocupadas or 0),
        lambda ocupacion, nuevo_total: setattr(ocupacion, "total_personas_ocupadas", nuevo_total),
        "La reserva no puede cancelarse porque la ocupacion global es inconsistente",
    )


def _decrementar_ocupaciones(
    reserva_repo: ReservaRepository,
    ocupaciones: list,
    cantidad: int,
    obtener_actual,
    asignar_nuevo_total,
    mensaje_error: str,
) -> None:
    total_ocupado = sum(obtener_actual(ocupacion) for ocupacion in ocupaciones)
    if total_ocupado < cantidad:
        raise HTTPException(status_code=409, detail=mensaje_error)

    restante = cantidad
    for ocupacion in ocupaciones:
        if restante == 0:
            break

        actual = obtener_actual(ocupacion)
        liberar = min(actual, restante)
        nuevo_total = actual - liberar
        if nuevo_total < 0:
            raise HTTPException(status_code=409, detail=mensaje_error)

        if nuevo_total == 0:
            reserva_repo.db.delete(ocupacion)
        else:
            asignar_nuevo_total(ocupacion, nuevo_total)
        restante -= liberar

    if restante != 0:
        raise HTTPException(status_code=409, detail=mensaje_error)


def _normalizar_monto(valor) -> Decimal:
    return Decimal(str(valor or 0)).quantize(_MONTO_CENTAVOS)


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

def completar_reserva(
    reserva_id: int,
    metodo_pago: MetodoPago,
    codigo_transaccion: Optional[str],
    proveedor: Proveedor,
    reserva_repo: ReservaRepository,
    pago_repo: PagoTransaccionRepository,
) -> dict:
    """
    Marca una reserva CONFIRMADA como COMPLETADA y registra el pago
    del saldo pendiente (90%) cobrado presencialmente.
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
        metodo_pago=metodo_pago,
        estado=EstadoPago.APROBADO,
        codigo_transaccion=codigo_transaccion,
    )
    pago_repo.db.add(pago)

    monto_pagado = float(reserva.monto_pendiente)
    reserva.monto_pendiente = 0
    reserva.estado = EstadoReserva.COMPLETADA

    pago_repo.db.commit()
    pago_repo.db.refresh(pago)

    return {
        "reserva_id": reserva.id,
        "estado": reserva.estado.value,
        "pago_id": pago.id,
        "monto_pagado": monto_pagado,
        "mensaje": "Reserva marcada como completada y saldo registrado correctamente.",
    }