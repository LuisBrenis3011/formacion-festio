from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, UTC
import logging

from app.domain.common.enums import EstadoPago, MetodoPago, TipoPago, TipoComprobante, RolUsuario
from app.domain.pagos.models import PagoTransaccion, Comprobante
from app.domain.reservas.models import Reserva, Evento, DetalleReserva
from app.domain.usuarios.models import Cliente, Proveedor, Usuario
from app.domain.pagos.schemas import PagoCreate, IniciarPagoMPRequest
from app.services.mercadopago_service import mp_client

logger = logging.getLogger(__name__)

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
    from app.repositories.notificacion_repository import NotificacionRepository
    
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

def iniciar_pago_mercadopago(
    datos: IniciarPagoMPRequest,
    email_cliente: str,
    usuario_id: int,
    db: Session,
) -> str:
    """
    Genera la preferencia de pago en Mercado Pago y retorna la URL de checkout.
    No crea registros en BD todavia; eso se hara cuando el webhook confirme el pago.
    """
    url_pago = mp_client.generar_preferencia(
        external_reference=datos.reserva_temp_id,
        monto=datos.monto,
        titulo_evento=datos.titulo_evento,
        email_cliente=email_cliente,
        reserva_temp_id=datos.reserva_temp_id,
        usuario_id=usuario_id,
        metodo_pago=datos.metodo_pago.value,
    )
    return url_pago

def procesar_webhook_mercadopago(datos_webhook: dict, db: Session):
    """
    Procesa notificaciones IPN de Mercado Pago.
    Flujo:
      1. Extrae el payment_id del webhook.
      2. Verifica el pago contra la API de MP (anti-spoofing).
      3. Si approved  -> crea reserva en BD desde Redis + pago + comprobante + notifica.
      4. Si rejected  -> libera bloqueo Redis.
    """
    from app.services import bloqueo_service
    from app.services.reserva import checkout_service, calculo_service
    from app.services import notificacion_service
    from app.repositories.catalogo_repository import ServicioProductoRepository
    from app.repositories.disponibilidad_repository import OcupacionServicioProductoRepository, OcupacionGlobalProveedorRepository
    from app.repositories.notificacion_repository import NotificacionRepository

    mp_payment_id = datos_webhook.get("data", {}).get("id")
    if not mp_payment_id:
        return

    try:
        payment_info = mp_client.obtener_pago(int(mp_payment_id))
    except Exception:
        logger.exception("Error verificando pago en MP para webhook")
        return

    estado_mp = payment_info.get("status")
    metadata = payment_info.get("metadata", {})
    reserva_temp_id = metadata.get("reserva_temp_id")
    usuario_id = metadata.get("usuario_id")
    metodo_pago_str = metadata.get("metodo_pago", "TARJETA")

    if not reserva_temp_id or not usuario_id:
        logger.warning("Webhook sin reserva_temp_id o usuario_id en metadata")
        return

    datos_bloqueo = bloqueo_service.obtener_bloqueo(reserva_temp_id)
    if not datos_bloqueo:
        logger.warning("Redis lock expirado para reserva_temp_id=%s", reserva_temp_id)
        return

    if estado_mp == "approved":
        _confirmar_reserva_desde_webhook(
            datos_bloqueo=datos_bloqueo,
            usuario_id=int(usuario_id),
            payment_info=payment_info,
            metodo_pago_str=metodo_pago_str,
            db=db,
        )

    elif estado_mp in ("rejected", "cancelled"):
        bloqueo_service.liberar_bloqueo(reserva_temp_id)
        logger.info("Pago rechazado/cancelado, bloqueo liberado para reserva_temp_id=%s", reserva_temp_id)


def _confirmar_reserva_desde_webhook(
    datos_bloqueo: dict,
    usuario_id: int,
    payment_info: dict,
    metodo_pago_str: str,
    db: Session,
):
    """
    Crea todos los registros en BD a partir del bloqueo Redis cuando el pago es aprobado.
    Soporta dos formatos de Redis:
      - prebloquear (publico): tiene clave "evento" con datos del evento
      - iniciar_reserva (auth): tiene clave "evento_id" con ID de evento existente
    """
    from app.services.reserva import checkout_service, calculo_service
    from app.services import bloqueo_service, notificacion_service
    from app.repositories.catalogo_repository import ServicioProductoRepository
    from app.repositories.disponibilidad_repository import OcupacionServicioProductoRepository, OcupacionGlobalProveedorRepository
    from app.repositories.notificacion_repository import NotificacionRepository

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or usuario.rol != RolUsuario.CLIENTE:
        logger.warning("Usuario %s no es un cliente valido", usuario_id)
        return

    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_id).first()
    if not cliente:
        cliente = Cliente(usuario_id=usuario_id)
        db.add(cliente)
        db.flush()

    if "evento_id" in datos_bloqueo:
        evento = db.query(Evento).filter(Evento.id == datos_bloqueo["evento_id"]).first()
        if not evento:
            logger.warning("Evento %s no encontrado", datos_bloqueo["evento_id"])
            return
        fecha_inicio = evento.fecha_evento_inicio
        fecha_fin = evento.fecha_evento_fin
    elif "evento" in datos_bloqueo:
        evento_data = datos_bloqueo["evento"]
        fecha_inicio = calculo_service.parse_datetime(evento_data["fecha_evento_inicio"])
        fecha_fin = calculo_service.parse_datetime(evento_data["fecha_evento_fin"])
        evento = Evento(
            cliente_id=cliente.id,
            nombre_evento=evento_data["nombre_evento"],
            tipo_evento=evento_data.get("tipo_evento"),
            fecha_evento_inicio=fecha_inicio,
            fecha_evento_fin=fecha_fin,
            direccion=evento_data["direccion"],
            aforo_estimado=evento_data.get("aforo_estimado"),
        )
        db.add(evento)
        db.flush()
    else:
        logger.warning("Redis blob sin datos de evento")
        return

    proveedor = db.query(Proveedor).filter(Proveedor.id == datos_bloqueo["proveedor_id"]).first()
    if not proveedor:
        logger.warning("Proveedor %s no encontrado", datos_bloqueo["proveedor_id"])
        return

    servicio_repo = ServicioProductoRepository(db)
    ocupacion_sp_repo = OcupacionServicioProductoRepository(db)
    ocupacion_global_repo = OcupacionGlobalProveedorRepository(db)

    items_ocupacion = datos_bloqueo.get("items_ocupacion", [])
    if items_ocupacion:
        observaciones = checkout_service._validar_disponibilidad_items(
            proveedor=proveedor,
            items_ocupacion=items_ocupacion,
            inicio=fecha_inicio,
            fin=fecha_fin,
            servicio_repo=servicio_repo,
            ocupacion_sp_repo=ocupacion_sp_repo,
            ocupacion_global_repo=ocupacion_global_repo,
            reserva_temp_id_actual=datos_bloqueo.get("reserva_temp_id"),
        )
        if observaciones:
            logger.warning("Inventario no disponible en webhook: %s", observaciones)
            bloqueo_service.liberar_bloqueo(datos_bloqueo["reserva_temp_id"])
            return

    codigo_transaccion = str(payment_info.get("id"))

    try:
        metodo_pago = MetodoPago(metodo_pago_str)
    except ValueError:
        metodo_pago = MetodoPago.TARJETA

    reserva = Reserva(
        evento_id=evento.id,
        proveedor_id=datos_bloqueo["proveedor_id"],
        estado="CONFIRMADA",
        monto_total=Decimal(str(datos_bloqueo["monto_total"])),
        costo_movilidad=Decimal("0.00"),
        monto_adelanto=Decimal(str(datos_bloqueo["monto_adelanto"])),
        monto_pendiente=Decimal(str(datos_bloqueo["monto_pendiente"])),
    )
    db.add(reserva)
    db.flush()

    for detalle_data in datos_bloqueo.get("detalles_reserva", []):
        db.add(DetalleReserva(
            reserva_id=reserva.id,
            paquete_id=detalle_data.get("paquete_id"),
            servicio_producto_id=detalle_data.get("servicio_producto_id"),
            cantidad=detalle_data.get("cantidad", 1),
            horas_contratadas=detalle_data.get("horas_contratadas"),
            precio_unitario=Decimal(str(detalle_data["precio_unitario"])),
            subtotal=Decimal(str(detalle_data["subtotal"])),
            fecha_hora_inicio_servicio=fecha_inicio,
            fecha_hora_fin_servicio=fecha_fin,
        ))

    for item in items_ocupacion:
        checkout_service._actualizar_ocupacion_item(
            servicio_producto_id=item["servicio_producto_id"],
            cantidad=item["cantidad"],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            ocupacion_sp_repo=ocupacion_sp_repo,
        )

    personas = int(datos_bloqueo.get("personas_requeridas") or 0)
    if personas:
        checkout_service._actualizar_ocupacion_global(
            proveedor_id=datos_bloqueo["proveedor_id"],
            cantidad=personas,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            ocupacion_global_repo=ocupacion_global_repo,
        )

    pago = PagoTransaccion(
        reserva_id=reserva.id,
        tipo_pago=TipoPago.ADELANTO_ONLINE,
        monto=Decimal(str(datos_bloqueo["monto_adelanto"])),
        metodo_pago=metodo_pago,
        estado=EstadoPago.APROBADO,
        codigo_transaccion=codigo_transaccion,
        fecha_pago=datetime.now(UTC),
    )
    db.add(pago)
    db.flush()

    emitir_comprobante(
        reserva_id=reserva.id,
        pago_id=pago.id,
        tipo=TipoComprobante.BOLETA,
        db=db,
    )

    db.commit()

    bloqueo_service.liberar_bloqueo(datos_bloqueo["reserva_temp_id"])

    notificacion_service.notificar_confirmacion_reserva(
        usuario_cliente_id=usuario.id,
        usuario_proveedor_id=proveedor.usuario_id,
        reserva_id=reserva.id,
        repo=NotificacionRepository(db),
    )

    logger.info("Reserva confirmada via webhook MP: reserva_id=%s, pago_id=%s", reserva.id, pago.id)