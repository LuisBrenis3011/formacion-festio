from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.domain.common.enums   import EstadoPago, TipoComprobante
from app.domain.pagos.models    import PagoTransaccion, Comprobante
from app.domain.reservas.models import Reserva, Evento
from app.domain.usuarios.models import Cliente, Proveedor
from app.domain.pagos.schemas   import PagoCreate

from app.repositories.pago_repository import (
    PagoTransaccionRepository,
    ComprobanteRepository
)

from app.repositories.usuario_repository import (
    ClienteRepository,
    ProveedorRepository
)

from app.repositories.reserva_repository import (
    ReservaRepository,
    EventoRepository
)

def procesar_pago(
    datos: PagoCreate,
    pago_repo: PagoTransaccionRepository,
    reserva_repo: ReservaRepository,
) -> PagoTransaccion:
    reserva = reserva_repo.get(datos.reserva_id)

    if not reserva:
        raise HTTPException(
            status_code=404,
            detail="Reserva no encontrada"
        )

    pago = pago_repo.create({
        "reserva_id": datos.reserva_id,
        "tipo_pago": datos.tipo_pago,
        "monto": datos.monto,
        "metodo_pago": datos.metodo_pago,
        "estado": EstadoPago.PENDIENTE,
        "codigo_transaccion": datos.codigo_transaccion,
    })

    return pago


def aprobar_pago(
    pago_id: int,
    codigo_transaccion: str,
    pago_repo: PagoTransaccionRepository,
) -> PagoTransaccion:
    pago = pago_repo.get(pago_id)

    if not pago:
        raise HTTPException(
            status_code=404,
            detail="Pago no encontrado"
        )

    pago.estado = EstadoPago.APROBADO
    pago.codigo_transaccion = codigo_transaccion

    pago_repo.db.commit()
    pago_repo.db.refresh(pago)

    return pago


def aprobar_pago_completo(
    pago_id: int,
    reserva_temp_id: str,
    codigo_transaccion: str,
    db: Session,
) -> PagoTransaccion:
    """
    Orquesta el flujo completo de aprobación:
    1. Aprueba el pago
    2. Confirma la reserva definitiva en BD
    3. Emite el comprobante automáticamente
    4. Notifica a cliente y proveedor
    """
    from app.services.reserva import checkout_service
    from app.services import notificacion_service
    from app.repositories.reserva_repository import EventoRepository, ReservaRepository, DetalleReservaRepository
    from app.repositories.catalogo_repository import ServicioProductoRepository
    from app.repositories.disponibilidad_repository import OcupacionServicioProductoRepository, OcupacionGlobalProveedorRepository

    from app.repositories.notificacion_repository import NotificacionRepository
    
    # 1. Aprobar el pago
    pago_repo = PagoTransaccionRepository(db)

    pago = aprobar_pago(
        pago_id,
        codigo_transaccion,
        pago_repo
    )

    # 2. Confirmar la reserva (convierte bloqueo Redis → BD)
    reserva = checkout_service.confirmar_reserva(
        reserva_temp_id, 
        pago_id, 
        EventoRepository(db),
        ReservaRepository(db),
        DetalleReservaRepository(db),
        ServicioProductoRepository(db),
        OcupacionServicioProductoRepository(db),
        OcupacionGlobalProveedorRepository(db)
    )

    # 3. Emitir comprobante automáticamente
    emitir_comprobante(
        reserva_id=reserva.id,
        pago_id=pago.id,
        tipo=TipoComprobante.BOLETA,
        db=db,
    )

    # 4. Notificar a ambas partes
    evento    = db.query(Evento).filter(Evento.id == reserva.evento_id).first()
    cliente   = db.query(Cliente).filter(Cliente.id == evento.cliente_id).first()
    proveedor = db.query(Proveedor).filter(Proveedor.id == reserva.proveedor_id).first()

    repo_notificacion = NotificacionRepository(db)

    notificacion_service.notificar_confirmacion_reserva(
        usuario_cliente_id=cliente.usuario_id,
        usuario_proveedor_id=proveedor.usuario_id,
        reserva_id=reserva.id,
        repo=repo_notificacion,
    )

    return pago


def rechazar_pago(
    pago_id: int,
    pago_repo: PagoTransaccionRepository
) -> PagoTransaccion:

    pago = pago_repo.get(pago_id)

    if not pago:
        raise HTTPException(
            status_code=404,
            detail="Pago no encontrado"
        )

    pago.estado = EstadoPago.RECHAZADO

    pago_repo.db.commit()
    pago_repo.db.refresh(pago)

    return pago


def rechazar_pago_completo(
    pago_id: int, usuario_id: int, reserva_id: int, db: Session
) -> dict:
    """Marca el pago como rechazado y notifica al cliente."""
    from app.services import notificacion_service

    from app.repositories.notificacion_repository import ( NotificacionRepository )
    
    pago_repo = PagoTransaccionRepository(db)

    rechazar_pago(
        pago_id,
        pago_repo
    )
    
    repo_notificacion = NotificacionRepository(db)

    notificacion_service.notificar_fallo_pago(
        usuario_id,
        reserva_id,
        repo_notificacion
    )
    
    return {"mensaje": "Pago rechazado. El cliente puede reintentar."}


def obtener_comprobante(reserva_id: int, db: Session) -> Comprobante:
    """Retorna el comprobante de una reserva confirmada."""
    comprobante = db.query(Comprobante).filter(
        Comprobante.reserva_id == reserva_id
    ).first()
    if not comprobante:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    return comprobante


def emitir_comprobante(
    reserva_id: int,
    pago_id: int,
    tipo: str,
    db: Session
) -> Comprobante:

    serie = "B001" if tipo == "BOLETA" else "F001"

    comprobante = Comprobante(
        reserva_id=reserva_id,
        pago_id=pago_id,
        tipo=tipo,
        numero_comprobante="TEMP",
        url_pdf=None,
    )

    db.add(comprobante)
    db.flush()

    comprobante.numero_comprobante = (
        f"{serie}-{str(comprobante.id).zfill(8)}"
    )

    db.commit()
    db.refresh(comprobante)

    return comprobante