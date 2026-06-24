from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal
from typing import List
import uuid

from app.domain.reservas.models        import Evento, Reserva, DetalleReserva
from app.domain.catalogo.models       import DetallePaquete, ServicioProducto, Paquete
from app.domain.disponibilidad.models import OcupacionServicioProducto, OcupacionGlobalProveedor
from app.domain.common.enums          import EstadoBasico, EstadoPago, EstadoReserva, MetodoPago, RolUsuario, TipoPago
from app.domain.pagos.models           import PagoTransaccion
from app.domain.usuarios.models        import Cliente, Proveedor, Usuario
from app.domain.reservas.schemas       import (
    CheckoutClienteCreate,
    CheckoutReservaResponse,
    DetalleReservaCreate,
    EventoCreate,
    MisReservasDetalleOut,
    MisReservasItemOut,
    PreReservaCreate,
    PreReservaResponse,
    ReservaCreate,
)
from app.core.security         import hash_password, verify_password
from app.services              import disponibilidad_service, bloqueo_service


def crear_evento(datos: EventoCreate, db: Session) -> Evento:
    evento = Evento(**datos.model_dump())
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


def obtener_evento(evento_id: int, db: Session) -> Evento:
    """Busca un evento por ID. Lanza 404 si no existe."""
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


def eventos_por_cliente(cliente_id: int, db: Session) -> List[Evento]:
    """Historial de eventos de un cliente."""
    return db.query(Evento).filter(Evento.cliente_id == cliente_id).all()


def obtener_reserva(reserva_id: int, db: Session) -> Reserva:
    """Busca una reserva activa por ID. Lanza 404 si no existe o fue eliminada."""
    reserva = db.query(Reserva).filter(
        Reserva.id == reserva_id,
        Reserva.deleted_at == None
    ).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva


def cancelar_reserva(reserva_id: int, db: Session) -> dict:
    """Cancela una reserva confirmada (soft delete)."""
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if reserva.estado == EstadoReserva.COMPLETADA:
        raise HTTPException(
            status_code=400, detail="No se puede cancelar una reserva completada"
        )

    reserva.estado     = EstadoReserva.CANCELADA
    reserva.deleted_at = datetime.utcnow()
    db.commit()
    return {"mensaje": "Reserva cancelada correctamente"}


def prebloquear_reserva(datos: PreReservaCreate, db: Session) -> PreReservaResponse:
    if datos.fecha_evento_fin <= datos.fecha_evento_inicio:
        raise HTTPException(status_code=400, detail="La hora de fin debe ser posterior al inicio")

    proveedor = db.query(Proveedor).filter(Proveedor.id == datos.proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    paquete = db.query(Paquete).filter(
        Paquete.id == datos.paquete_id,
        Paquete.proveedor_id == datos.proveedor_id,
    ).first()
    if not paquete or paquete.estado != EstadoBasico.ACTIVO:
        raise HTTPException(status_code=404, detail="Paquete activo no encontrado para el proveedor")

    detalles_reserva, items_ocupacion, monto_total = _construir_carrito(datos, paquete, db)
    observaciones = _validar_disponibilidad_items(
        proveedor=proveedor,
        items_ocupacion=items_ocupacion,
        inicio=datos.fecha_evento_inicio,
        fin=datos.fecha_evento_fin,
        db=db,
    )
    if observaciones:
        raise HTTPException(status_code=409, detail={"mensaje": "Inventario no disponible", "items": observaciones})

    monto_adelanto = round(monto_total * 0.10, 2)
    monto_pendiente = round(monto_total * 0.90, 2)
    reserva_temp_id = str(uuid.uuid4())

    bloqueo_service.crear_bloqueo(reserva_temp_id, {
        "flujo": "publico_checkout",
        "reserva_temp_id": reserva_temp_id,
        "proveedor_id": datos.proveedor_id,
        "paquete_id": datos.paquete_id,
        "evento": {
            "nombre_evento": datos.nombre_evento,
            "tipo_evento": datos.tipo_evento,
            "fecha_evento_inicio": datos.fecha_evento_inicio.isoformat(),
            "fecha_evento_fin": datos.fecha_evento_fin.isoformat(),
            "direccion": datos.direccion,
            "aforo_estimado": datos.aforo_estimado,
        },
        "detalles_reserva": detalles_reserva,
        "items_ocupacion": items_ocupacion,
        "personas_requeridas": _personas_requeridas(items_ocupacion, db),
        "monto_total": monto_total,
        "monto_adelanto": monto_adelanto,
        "monto_pendiente": monto_pendiente,
    })

    return PreReservaResponse(
        reserva_temp_id=reserva_temp_id,
        proveedor_id=datos.proveedor_id,
        paquete_id=datos.paquete_id,
        monto_total=monto_total,
        monto_adelanto=monto_adelanto,
        monto_pendiente=monto_pendiente,
        minutos_restantes=10,
        detalles=detalles_reserva,
        mensaje="Inventario bloqueado por 10 minutos. Completa el pago simulado del adelanto.",
    )


def confirmar_checkout_simulado(
    reserva_temp_id: str,
    datos: CheckoutClienteCreate,
    db: Session,
    usuario_autenticado: Usuario | None = None,
) -> CheckoutReservaResponse:
    bloqueado = bloqueo_service.obtener_bloqueo(reserva_temp_id)
    if not bloqueado:
        raise HTTPException(status_code=408, detail="El bloqueo expiró o no existe")

    metodo_pago = _validar_metodo_pago(datos.metodo_pago)
    cliente = _obtener_cliente_checkout(datos, db, usuario_autenticado)
    evento_data = bloqueado["evento"]
    fecha_inicio = _parse_datetime(evento_data["fecha_evento_inicio"])
    fecha_fin = _parse_datetime(evento_data["fecha_evento_fin"])

    proveedor = db.query(Proveedor).filter(Proveedor.id == bloqueado["proveedor_id"]).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    observaciones = _validar_disponibilidad_items(
        proveedor=proveedor,
        items_ocupacion=bloqueado["items_ocupacion"],
        inicio=fecha_inicio,
        fin=fecha_fin,
        db=db,
        reserva_temp_id_actual=reserva_temp_id,
    )
    if observaciones:
        raise HTTPException(status_code=409, detail={"mensaje": "Inventario ya no disponible", "items": observaciones})

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

    reserva = Reserva(
        evento_id=evento.id,
        proveedor_id=bloqueado["proveedor_id"],
        estado="CONFIRMADA",
        monto_total=Decimal(str(bloqueado["monto_total"])),
        costo_movilidad=Decimal("0.00"),
        monto_adelanto=Decimal(str(bloqueado["monto_adelanto"])),
        monto_pendiente=Decimal(str(bloqueado["monto_pendiente"])),
    )
    db.add(reserva)
    db.flush()

    for detalle_data in bloqueado["detalles_reserva"]:
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

    for item in bloqueado["items_ocupacion"]:
        _actualizar_ocupacion_item(
            servicio_producto_id=item["servicio_producto_id"],
            cantidad=item["cantidad"],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            db=db,
        )

    personas = int(bloqueado.get("personas_requeridas") or 0)
    if personas:
        _actualizar_ocupacion_global(
            proveedor_id=bloqueado["proveedor_id"],
            cantidad=personas,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            db=db,
        )

    pago = PagoTransaccion(
        reserva_id=reserva.id,
        tipo_pago=TipoPago.ADELANTO_ONLINE,
        monto=Decimal(str(bloqueado["monto_adelanto"])),
        metodo_pago=metodo_pago,
        estado=EstadoPago.APROBADO,
        codigo_transaccion=f"SIM-{uuid.uuid4().hex[:12].upper()}",
        fecha_pago=datetime.utcnow(),
    )
    db.add(pago)
    db.commit()
    db.refresh(reserva)
    db.refresh(pago)
    bloqueo_service.liberar_bloqueo(reserva_temp_id)

    return CheckoutReservaResponse(
        reserva_id=reserva.id,
        evento_id=evento.id,
        cliente_id=cliente.id,
        pago_id=pago.id,
        estado_pago=EstadoPago.APROBADO.value,
        monto_total=float(reserva.monto_total),
        monto_adelanto=float(reserva.monto_adelanto),
        monto_pendiente=float(reserva.monto_pendiente),
        mensaje="Reserva confirmada con pago simulado del adelanto.",
    )


def iniciar_reserva(datos: ReservaCreate, db: Session) -> dict:
    """
    Paso 1: Valida disponibilidad y crea el bloqueo en Redis.
    No escribe nada en la BD todavía.
    Retorna un ID temporal para rastrear el bloqueo.
    """
    evento = db.query(Evento).filter(Evento.id == datos.evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Verificar disponibilidad en tiempo real
    resultado = disponibilidad_service.consultar_disponibilidad(
        proveedor_id = datos.proveedor_id,
        fecha_inicio = evento.fecha_evento_inicio,
        fecha_fin    = evento.fecha_evento_fin,
        detalles     = datos.detalles,
        db           = db,
    )

    if not resultado.disponible:
        raise HTTPException(
            status_code=409,
            detail={"mensaje": resultado.mensaje, "items": resultado.items_no_disponibles}
        )

    # Calcular montos
    monto_total = _calcular_monto_total(datos.detalles, db)
    monto_adelanto  = round(monto_total * 0.10, 2)
    monto_pendiente = round(monto_total * 0.90, 2)

    # Crear bloqueo temporal en Redis
    import uuid
    reserva_temp_id = str(uuid.uuid4())

    bloqueo_service.crear_bloqueo(reserva_temp_id, {
        "evento_id"    : datos.evento_id,
        "proveedor_id" : datos.proveedor_id,
        "detalles"     : [d.model_dump() for d in datos.detalles],
        "monto_total"  : monto_total,
        "monto_adelanto"  : monto_adelanto,
        "monto_pendiente" : monto_pendiente,
    })

    return {
        "reserva_temp_id" : reserva_temp_id,
        "monto_total"     : monto_total,
        "monto_adelanto"  : monto_adelanto,
        "monto_pendiente" : monto_pendiente,
        "minutos_restantes": 10,
        "mensaje"         : "Inventario bloqueado. Tienes 10 minutos para completar el adelanto.",
    }


def confirmar_reserva(reserva_temp_id: str, pago_id: int, db: Session) -> Reserva:
    """
    Paso 2: Llamado después de validar el pago exitoso.
    Convierte el bloqueo temporal en reserva definitiva en la BD.
    """
    datos_bloqueo = bloqueo_service.obtener_bloqueo(reserva_temp_id)
    if not datos_bloqueo:
        raise HTTPException(
            status_code=408,
            detail="El tiempo de bloqueo expiró. Por favor reinicia la reserva."
        )

    evento = db.query(Evento).filter(Evento.id == datos_bloqueo["evento_id"]).first()

    # Crear la reserva en BD
    reserva = Reserva(
        evento_id       = datos_bloqueo["evento_id"],
        proveedor_id    = datos_bloqueo["proveedor_id"],
        estado          = EstadoReserva.CONFIRMADA,
        monto_total     = datos_bloqueo["monto_total"],
        monto_adelanto  = datos_bloqueo["monto_adelanto"],
        monto_pendiente = datos_bloqueo["monto_pendiente"],
    )
    db.add(reserva)
    db.flush()

    # Crear detalles de la reserva
    for d in datos_bloqueo["detalles"]:
        if d.get("servicio_producto_id"):
            servicio = db.query(ServicioProducto).filter(
                ServicioProducto.id == d["servicio_producto_id"]
            ).first()
            precio   = float(servicio.precio_unitario)
            subtotal = precio * d["cantidad"]

            detalle = DetalleReserva(
                reserva_id           = reserva.id,
                servicio_producto_id = d["servicio_producto_id"],
                cantidad             = d["cantidad"],
                horas_contratadas    = d.get("horas_contratadas"),
                precio_unitario      = precio,
                subtotal             = subtotal,
                fecha_hora_inicio_servicio = evento.fecha_evento_inicio,
                fecha_hora_fin_servicio    = evento.fecha_evento_fin,
            )
            db.add(detalle)

            # Actualizar ocupación del ítem
            _actualizar_ocupacion_item(
                servicio_producto_id = d["servicio_producto_id"],
                cantidad             = d["cantidad"],
                fecha_inicio         = evento.fecha_evento_inicio,
                fecha_fin            = evento.fecha_evento_fin,
                db                   = db,
            )

            # Actualizar ocupación global si requiere persona
            if servicio.requiere_persona:
                _actualizar_ocupacion_global(
                    proveedor_id = datos_bloqueo["proveedor_id"],
                    cantidad     = d["cantidad"],
                    fecha_inicio = evento.fecha_evento_inicio,
                    fecha_fin    = evento.fecha_evento_fin,
                    db           = db,
                )

    db.commit()
    db.refresh(reserva)

    # Liberar el bloqueo en Redis
    bloqueo_service.liberar_bloqueo(reserva_temp_id)

    return reserva


def _calcular_monto_total(detalles, db: Session) -> float:
    total = 0.0
    for d in detalles:
        if d.servicio_producto_id:
            servicio = db.query(ServicioProducto).filter(
                ServicioProducto.id == d.servicio_producto_id
            ).first()
            if servicio:
                horas    = d.horas_contratadas or servicio.duracion_base_horas or 1
                total   += float(servicio.precio_unitario) * d.cantidad * horas
        elif d.paquete_id:
            paquete = db.query(Paquete).filter(Paquete.id == d.paquete_id).first()
            if paquete:
                total += float(paquete.precio_base)
    return round(total, 2)


def _construir_carrito(datos: PreReservaCreate, paquete: Paquete, db: Session):
    detalles_reserva = [{
        "paquete_id": paquete.id,
        "servicio_producto_id": None,
        "nombre": paquete.nombre,
        "tipo": "PAQUETE",
        "cantidad": 1,
        "horas_contratadas": None,
        "precio_unitario": float(paquete.precio_base or 0),
        "subtotal": float(paquete.precio_base or 0),
    }]
    items_ocupacion = []

    detalles_paquete = db.query(DetallePaquete).filter(
        DetallePaquete.paquete_id == paquete.id
    ).all()
    for detalle in detalles_paquete:
        if not detalle.servicio_producto_id:
            continue
        items_ocupacion.append({
            "servicio_producto_id": detalle.servicio_producto_id,
            "cantidad": int(detalle.cantidad_incluida or 1),
        })

    total = float(paquete.precio_base or 0)
    for adicional in datos.adicionales:
        servicio = db.query(ServicioProducto).filter(
            ServicioProducto.id == adicional.servicio_producto_id,
            ServicioProducto.proveedor_id == datos.proveedor_id,
            ServicioProducto.deleted_at == None,
        ).first()
        if not servicio or servicio.estado != EstadoBasico.ACTIVO:
            raise HTTPException(
                status_code=404,
                detail=f"Servicio adicional {adicional.servicio_producto_id} no disponible para el proveedor",
            )

        horas = adicional.horas_contratadas
        if horas is None and servicio.duracion_base_horas is not None:
            horas = float(servicio.duracion_base_horas)
        subtotal = _subtotal_servicio(servicio, adicional.cantidad, horas)
        total += subtotal
        detalles_reserva.append({
            "paquete_id": None,
            "servicio_producto_id": servicio.id,
            "nombre": servicio.nombre,
            "tipo": "ADICIONAL",
            "cantidad": adicional.cantidad,
            "horas_contratadas": horas,
            "precio_unitario": float(servicio.precio_unitario or 0),
            "subtotal": subtotal,
        })
        items_ocupacion.append({
            "servicio_producto_id": servicio.id,
            "cantidad": adicional.cantidad,
        })

    return detalles_reserva, items_ocupacion, round(total, 2)


def _subtotal_servicio(servicio: ServicioProducto, cantidad: int, horas: float | None) -> float:
    precio = float(servicio.precio_unitario or 0)
    if horas and (servicio.requiere_persona or "DJ" in (servicio.nombre or "").upper()):
        return round(precio * cantidad * horas, 2)
    return round(precio * cantidad, 2)


def _validar_disponibilidad_items(
    proveedor: Proveedor,
    items_ocupacion: list[dict],
    inicio: datetime,
    fin: datetime,
    db: Session,
    reserva_temp_id_actual: str | None = None,
) -> list[str]:
    observaciones = []
    cantidades = _agrupar_items(items_ocupacion)

    for servicio_id, cantidad in cantidades.items():
        servicio = db.query(ServicioProducto).filter(
            ServicioProducto.id == servicio_id,
            ServicioProducto.proveedor_id == proveedor.id,
        ).first()
        if not servicio:
            observaciones.append(f"Servicio {servicio_id} no pertenece al proveedor.")
            continue

        ocupacion_db = db.query(OcupacionServicioProducto).filter(
            OcupacionServicioProducto.servicio_producto_id == servicio_id,
            OcupacionServicioProducto.fecha_hora_inicio < fin,
            OcupacionServicioProducto.fecha_hora_fin > inicio,
        ).all()
        ocupado = sum(int(o.cantidad_ocupada or 0) for o in ocupacion_db)
        ocupado += _cantidad_bloqueada_temporal(
            servicio_id=servicio_id,
            inicio=inicio,
            fin=fin,
            reserva_temp_id_actual=reserva_temp_id_actual,
        )
        disponible = int(servicio.stock_maximo_simultaneo or 0) - ocupado
        if disponible < cantidad:
            observaciones.append(
                f"{servicio.nombre}: disponible {disponible}, solicitado {cantidad}."
            )

    requeridas = _personas_requeridas(items_ocupacion, db)
    if requeridas:
        ocupacion_global = db.query(OcupacionGlobalProveedor).filter(
            OcupacionGlobalProveedor.proveedor_id == proveedor.id,
            OcupacionGlobalProveedor.fecha_hora_inicio < fin,
            OcupacionGlobalProveedor.fecha_hora_fin > inicio,
        ).all()
        ocupadas = sum(int(o.total_personas_ocupadas or 0) for o in ocupacion_global)
        ocupadas += _personas_bloqueadas_temporal(
            proveedor_id=proveedor.id,
            inicio=inicio,
            fin=fin,
            reserva_temp_id_actual=reserva_temp_id_actual,
        )
        disponibles = int(proveedor.capacidad_humana_total or 0) - ocupadas
        if disponibles < requeridas:
            observaciones.append(
                f"Capacidad humana del proveedor: disponible {disponibles}, solicitado {requeridas}."
            )

    return observaciones


def _agrupar_items(items: list[dict]) -> dict[int, int]:
    agrupados = {}
    for item in items:
        servicio_id = int(item["servicio_producto_id"])
        agrupados[servicio_id] = agrupados.get(servicio_id, 0) + int(item.get("cantidad") or 0)
    return agrupados


def _cantidad_bloqueada_temporal(
    servicio_id: int,
    inicio: datetime,
    fin: datetime,
    reserva_temp_id_actual: str | None,
) -> int:
    total = 0
    for bloqueo in bloqueo_service.listar_bloqueos():
        if _es_bloqueo_actual(bloqueo, reserva_temp_id_actual):
            continue
        evento = bloqueo.get("evento", {})
        if not _se_solapan(inicio, fin, evento.get("fecha_evento_inicio"), evento.get("fecha_evento_fin")):
            continue
        for item in bloqueo.get("items_ocupacion", []):
            if int(item.get("servicio_producto_id")) == servicio_id:
                total += int(item.get("cantidad") or 0)
    return total


def _personas_bloqueadas_temporal(
    proveedor_id: int,
    inicio: datetime,
    fin: datetime,
    reserva_temp_id_actual: str | None,
) -> int:
    total = 0
    for bloqueo in bloqueo_service.listar_bloqueos():
        if _es_bloqueo_actual(bloqueo, reserva_temp_id_actual):
            continue
        if int(bloqueo.get("proveedor_id") or 0) != proveedor_id:
            continue
        evento = bloqueo.get("evento", {})
        if _se_solapan(inicio, fin, evento.get("fecha_evento_inicio"), evento.get("fecha_evento_fin")):
            total += int(bloqueo.get("personas_requeridas") or 0)
    return total


def _es_bloqueo_actual(bloqueo: dict, reserva_temp_id_actual: str | None) -> bool:
    return bool(reserva_temp_id_actual and bloqueo.get("reserva_temp_id") == reserva_temp_id_actual)


def _personas_requeridas(items_ocupacion: list[dict], db: Session) -> int:
    total = 0
    for servicio_id, cantidad in _agrupar_items(items_ocupacion).items():
        servicio = db.query(ServicioProducto).filter(ServicioProducto.id == servicio_id).first()
        if servicio and servicio.requiere_persona:
            total += cantidad
    return total


def _se_solapan(inicio: datetime, fin: datetime, otro_inicio, otro_fin) -> bool:
    if not otro_inicio or not otro_fin:
        return False
    return _parse_datetime(otro_inicio) < fin and _parse_datetime(otro_fin) > inicio


def _parse_datetime(valor) -> datetime:
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))


def _obtener_cliente_checkout(
    datos: CheckoutClienteCreate,
    db: Session,
    usuario_autenticado: Usuario | None = None,
) -> Cliente:
    if not usuario_autenticado:
        return _crear_o_validar_cliente(datos, db)

    if usuario_autenticado.rol != RolUsuario.CLIENTE:
        raise HTTPException(status_code=400, detail="La sesión autenticada no pertenece a un cliente")
    if usuario_autenticado.estado == EstadoBasico.INACTIVO:
        raise HTTPException(status_code=403, detail="Cuenta inactiva")

    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario_autenticado.id).first()
    if not cliente:
        cliente = Cliente(
            usuario_id=usuario_autenticado.id,
            direccion=datos.direccion,
        )
        db.add(cliente)
        db.flush()
    elif datos.direccion and not cliente.direccion:
        cliente.direccion = datos.direccion

    return cliente


def _crear_o_validar_cliente(datos: CheckoutClienteCreate, db: Session) -> Cliente:
    if not datos.email or not datos.password or not datos.nombre:
        raise HTTPException(
            status_code=400,
            detail="Se requiere nombre, email y password para usuarios no autenticados",
        )
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if usuario:
        if usuario.rol != RolUsuario.CLIENTE:
            raise HTTPException(status_code=400, detail="El email pertenece a un usuario que no es cliente")
        if not verify_password(datos.password, usuario.contrasena_hash):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta para el email indicado")
    else:
        usuario = Usuario(
            nombre=datos.nombre,
            apellido=datos.apellido,
            email=datos.email,
            telefono=datos.telefono,
            contrasena_hash=hash_password(datos.password),
            rol=RolUsuario.CLIENTE,
            estado=EstadoBasico.ACTIVO,
        )
        db.add(usuario)
        db.flush()

    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario.id).first()
    if not cliente:
        cliente = Cliente(
            usuario_id=usuario.id,
            direccion=datos.direccion,
        )
        db.add(cliente)
        db.flush()
    elif datos.direccion and not cliente.direccion:
        cliente.direccion = datos.direccion

    return cliente


def _validar_metodo_pago(valor: str) -> MetodoPago:
    try:
        return MetodoPago(valor)
    except ValueError:
        validos = ", ".join(m.value for m in MetodoPago)
        raise HTTPException(status_code=400, detail=f"Método de pago inválido. Usa: {validos}")


def _actualizar_ocupacion_item(
    servicio_producto_id: int, cantidad: int,
    fecha_inicio: datetime, fecha_fin: datetime, db: Session
):
    ocupacion = db.query(OcupacionServicioProducto).filter(
        OcupacionServicioProducto.servicio_producto_id == servicio_producto_id,
        OcupacionServicioProducto.fecha_hora_inicio    == fecha_inicio,
        OcupacionServicioProducto.fecha_hora_fin       == fecha_fin,
    ).first()

    if ocupacion:
        ocupacion.cantidad_ocupada += cantidad
    else:
        db.add(OcupacionServicioProducto(
            servicio_producto_id = servicio_producto_id,
            fecha_hora_inicio    = fecha_inicio,
            fecha_hora_fin       = fecha_fin,
            cantidad_ocupada     = cantidad,
        ))


def _actualizar_ocupacion_global(
    proveedor_id: int, cantidad: int,
    fecha_inicio: datetime, fecha_fin: datetime, db: Session
):
    ocupacion = db.query(OcupacionGlobalProveedor).filter(
        OcupacionGlobalProveedor.proveedor_id      == proveedor_id,
        OcupacionGlobalProveedor.fecha_hora_inicio == fecha_inicio,
        OcupacionGlobalProveedor.fecha_hora_fin    == fecha_fin,
    ).first()

    if ocupacion:
        ocupacion.total_personas_ocupadas += cantidad
    else:
        db.add(OcupacionGlobalProveedor(
            proveedor_id            = proveedor_id,
            fecha_hora_inicio       = fecha_inicio,
            fecha_hora_fin          = fecha_fin,
            total_personas_ocupadas = cantidad,
        ))


def listar_mis_reservas(usuario: Usuario, db: Session) -> List[MisReservasItemOut]:
    """Devuelve todas las reservas del cliente autenticado, con detalles del evento y proveedor."""
    cliente = db.query(Cliente).filter(Cliente.usuario_id == usuario.id).first()
    if not cliente:
        return []

    eventos = db.query(Evento).filter(Evento.cliente_id == cliente.id).all()
    evento_ids = [e.id for e in eventos]
    if not evento_ids:
        return []

    reservas = (
        db.query(Reserva)
        .filter(Reserva.evento_id.in_(evento_ids), Reserva.deleted_at.is_(None))
        .order_by(Reserva.fecha_creacion.desc())
        .all()
    )

    resultado: List[MisReservasItemOut] = []
    for reserva in reservas:
        evento = next((e for e in eventos if e.id == reserva.evento_id), None)
        if not evento:
            continue

        proveedor = db.query(Proveedor).filter(Proveedor.id == reserva.proveedor_id).first()
        nombre_empresa = proveedor.nombre_empresa if proveedor else "Proveedor"

        detalles_out: List[MisReservasDetalleOut] = []
        for det in reserva.detalles:
            if det.deleted_at:
                continue
            if det.paquete_id:
                paq = db.query(Paquete).filter(Paquete.id == det.paquete_id).first()
                nombre = paq.nombre if paq else f"Paquete #{det.paquete_id}"
                tipo = "paquete"
            else:
                sp = db.query(ServicioProducto).filter(ServicioProducto.id == det.servicio_producto_id).first()
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
