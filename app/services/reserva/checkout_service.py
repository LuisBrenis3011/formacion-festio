import uuid
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException

from app.domain.reservas.models import Evento, Reserva, DetalleReserva
from app.domain.catalogo.models import Paquete, ServicioProducto
from app.domain.disponibilidad.models import OcupacionServicioProducto, OcupacionGlobalProveedor
from app.domain.common.enums import EstadoBasico, EstadoPago, EstadoReserva, MetodoPago, RolUsuario, TipoPago
from app.domain.pagos.models import PagoTransaccion
from app.domain.usuarios.models import Cliente, Proveedor, Usuario
from app.domain.reservas.schemas import (
    CheckoutClienteCreate,
    CheckoutReservaResponse,
    PreReservaCreate,
    PreReservaResponse,
    ReservaCreate,
)
from app.core.security import hash_password, verify_password
from app.services import bloqueo_service, disponibilidad_service
from app.services.reserva import calculo_service

from app.repositories.usuario_repository import ProveedorRepository, ClienteRepository, UsuarioRepository
from app.repositories.catalogo_repository import PaqueteRepository, ServicioProductoRepository, DetallePaqueteRepository
from app.repositories.reserva_repository import EventoRepository, ReservaRepository, DetalleReservaRepository
from app.repositories.pago_repository import PagoTransaccionRepository
from app.repositories.disponibilidad_repository import OcupacionServicioProductoRepository, OcupacionGlobalProveedorRepository

def prebloquear_reserva(
    datos: PreReservaCreate,
    proveedor_repo: ProveedorRepository,
    paquete_repo: PaqueteRepository,
    servicio_repo: ServicioProductoRepository,
    detalle_paquete_repo: DetallePaqueteRepository,
    ocupacion_sp_repo: OcupacionServicioProductoRepository,
    ocupacion_global_repo: OcupacionGlobalProveedorRepository
) -> PreReservaResponse:

    proveedor = proveedor_repo.get(datos.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    paquete = paquete_repo.db.query(Paquete).filter(
        Paquete.id == datos.paquete_id,
        Paquete.proveedor_id == datos.proveedor_id,
    ).first()
    if not paquete or paquete.estado != EstadoBasico.ACTIVO:
        raise HTTPException(status_code=404, detail="Paquete activo no encontrado para el proveedor")

    detalles_reserva, items_ocupacion, monto_total = calculo_service.construir_carrito(datos, paquete, servicio_repo, detalle_paquete_repo)
    observaciones = _validar_disponibilidad_items(
        proveedor=proveedor,
        items_ocupacion=items_ocupacion,
        inicio=datos.fecha_evento_inicio,
        fin=datos.fecha_evento_fin,
        servicio_repo=servicio_repo,
        ocupacion_sp_repo=ocupacion_sp_repo,
        ocupacion_global_repo=ocupacion_global_repo,
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
        "personas_requeridas": calculo_service.personas_requeridas(items_ocupacion, servicio_repo),
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
    usuario_autenticado: Usuario | None,
    cliente_repo: ClienteRepository,
    usuario_repo: UsuarioRepository,
    proveedor_repo: ProveedorRepository,
    servicio_repo: ServicioProductoRepository,
    ocupacion_sp_repo: OcupacionServicioProductoRepository,
    ocupacion_global_repo: OcupacionGlobalProveedorRepository,
    evento_repo: EventoRepository,
    reserva_repo: ReservaRepository,
    detalle_reserva_repo: DetalleReservaRepository,
    pago_repo: PagoTransaccionRepository
) -> CheckoutReservaResponse:
    bloqueado = bloqueo_service.obtener_bloqueo(reserva_temp_id)
    if not bloqueado:
        raise HTTPException(status_code=408, detail="El bloqueo expiró o no existe")

    metodo_pago = _validar_metodo_pago(datos.metodo_pago)
    cliente = _obtener_cliente_checkout(datos, cliente_repo, usuario_repo, usuario_autenticado)
    evento_data = bloqueado["evento"]
    fecha_inicio = calculo_service.parse_datetime(evento_data["fecha_evento_inicio"])
    fecha_fin = calculo_service.parse_datetime(evento_data["fecha_evento_fin"])

    proveedor = proveedor_repo.get(bloqueado["proveedor_id"])
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    observaciones = _validar_disponibilidad_items(
        proveedor=proveedor,
        items_ocupacion=bloqueado["items_ocupacion"],
        inicio=fecha_inicio,
        fin=fecha_fin,
        servicio_repo=servicio_repo,
        ocupacion_sp_repo=ocupacion_sp_repo,
        ocupacion_global_repo=ocupacion_global_repo,
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
    evento_repo.db.add(evento)
    evento_repo.db.flush()

    reserva = Reserva(
        evento_id=evento.id,
        proveedor_id=bloqueado["proveedor_id"],
        estado="CONFIRMADA",
        monto_total=Decimal(str(bloqueado["monto_total"])),
        costo_movilidad=Decimal("0.00"),
        monto_adelanto=Decimal(str(bloqueado["monto_adelanto"])),
        monto_pendiente=Decimal(str(bloqueado["monto_pendiente"])),
    )
    reserva_repo.db.add(reserva)
    reserva_repo.db.flush()

    for detalle_data in bloqueado["detalles_reserva"]:
        detalle_reserva_repo.db.add(DetalleReserva(
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
            ocupacion_sp_repo=ocupacion_sp_repo,
        )

    personas = int(bloqueado.get("personas_requeridas") or 0)
    if personas:
        _actualizar_ocupacion_global(
            proveedor_id=bloqueado["proveedor_id"],
            cantidad=personas,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            ocupacion_global_repo=ocupacion_global_repo,
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
    pago_repo.db.add(pago)
    pago_repo.db.commit()
    reserva_repo.db.refresh(reserva)
    pago_repo.db.refresh(pago)
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

def iniciar_reserva(
    datos: ReservaCreate,
    evento_repo: EventoRepository,
    paquete_repo: PaqueteRepository,
    servicio_repo: ServicioProductoRepository
) -> dict:
    evento = evento_repo.get(datos.evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    resultado = disponibilidad_service.consultar_disponibilidad(
        proveedor_id = datos.proveedor_id,
        fecha_inicio = evento.fecha_evento_inicio,
        fecha_fin    = evento.fecha_evento_fin,
        detalles     = datos.detalles,
        db           = evento_repo.db,
    )

    if not resultado.disponible:
        raise HTTPException(
            status_code=409,
            detail={"mensaje": resultado.mensaje, "items": resultado.items_no_disponibles}
        )

    monto_total = calculo_service.calcular_monto_total(datos.detalles, paquete_repo, servicio_repo)
    monto_adelanto  = round(monto_total * 0.10, 2)
    monto_pendiente = round(monto_total * 0.90, 2)

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

def confirmar_reserva(
    reserva_temp_id: str,
    pago_id: int,
    evento_repo: EventoRepository,
    reserva_repo: ReservaRepository,
    detalle_reserva_repo: DetalleReservaRepository,
    servicio_repo: ServicioProductoRepository,
    ocupacion_sp_repo: OcupacionServicioProductoRepository,
    ocupacion_global_repo: OcupacionGlobalProveedorRepository
) -> Reserva:
    datos_bloqueo = bloqueo_service.obtener_bloqueo(reserva_temp_id)
    if not datos_bloqueo:
        raise HTTPException(
            status_code=408,
            detail="El tiempo de bloqueo expiró. Por favor reinicia la reserva."
        )

    evento = evento_repo.get(datos_bloqueo["evento_id"])

    reserva = Reserva(
        evento_id       = datos_bloqueo["evento_id"],
        proveedor_id    = datos_bloqueo["proveedor_id"],
        estado          = EstadoReserva.CONFIRMADA,
        monto_total     = datos_bloqueo["monto_total"],
        monto_adelanto  = datos_bloqueo["monto_adelanto"],
        monto_pendiente = datos_bloqueo["monto_pendiente"],
    )
    reserva_repo.db.add(reserva)
    reserva_repo.db.flush()

    for d in datos_bloqueo["detalles"]:
        if d.get("servicio_producto_id"):
            servicio = servicio_repo.get(d["servicio_producto_id"])
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
            detalle_reserva_repo.db.add(detalle)

            _actualizar_ocupacion_item(
                servicio_producto_id = d["servicio_producto_id"],
                cantidad             = d["cantidad"],
                fecha_inicio         = evento.fecha_evento_inicio,
                fecha_fin            = evento.fecha_evento_fin,
                ocupacion_sp_repo    = ocupacion_sp_repo,
            )

            if servicio.requiere_persona:
                _actualizar_ocupacion_global(
                    proveedor_id = datos_bloqueo["proveedor_id"],
                    cantidad     = d["cantidad"],
                    fecha_inicio = evento.fecha_evento_inicio,
                    fecha_fin    = evento.fecha_evento_fin,
                    ocupacion_global_repo = ocupacion_global_repo,
                )

    reserva_repo.db.commit()
    reserva_repo.db.refresh(reserva)
    bloqueo_service.liberar_bloqueo(reserva_temp_id)

    return reserva

# --- Helpers locales ---

def _validar_disponibilidad_items(
    proveedor: Proveedor,
    items_ocupacion: list[dict],
    inicio: datetime,
    fin: datetime,
    servicio_repo: ServicioProductoRepository,
    ocupacion_sp_repo: OcupacionServicioProductoRepository,
    ocupacion_global_repo: OcupacionGlobalProveedorRepository,
    reserva_temp_id_actual: str | None = None,
) -> list[str]:
    observaciones = []
    cantidades = calculo_service.agrupar_items(items_ocupacion)

    for servicio_id, cantidad in cantidades.items():
        servicio = servicio_repo.db.query(ServicioProducto).filter(
            ServicioProducto.id == servicio_id,
            ServicioProducto.proveedor_id == proveedor.id,
        ).first()
        if not servicio:
            observaciones.append(f"Servicio {servicio_id} no pertenece al proveedor.")
            continue

        ocupacion_db = ocupacion_sp_repo.db.query(OcupacionServicioProducto).filter(
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

    requeridas = calculo_service.personas_requeridas(items_ocupacion, servicio_repo)
    if requeridas:
        ocupacion_global = ocupacion_global_repo.db.query(OcupacionGlobalProveedor).filter(
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
        if not calculo_service.se_solapan(inicio, fin, evento.get("fecha_evento_inicio"), evento.get("fecha_evento_fin")):
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
        if calculo_service.se_solapan(inicio, fin, evento.get("fecha_evento_inicio"), evento.get("fecha_evento_fin")):
            total += int(bloqueo.get("personas_requeridas") or 0)
    return total

def _es_bloqueo_actual(bloqueo: dict, reserva_temp_id_actual: str | None) -> bool:
    return bool(reserva_temp_id_actual and bloqueo.get("reserva_temp_id") == reserva_temp_id_actual)

def _obtener_cliente_checkout(
    datos: CheckoutClienteCreate,
    cliente_repo: ClienteRepository,
    usuario_repo: UsuarioRepository,
    usuario_autenticado: Usuario | None = None,
) -> Cliente:
    if not usuario_autenticado:
        return _crear_o_validar_cliente(datos, cliente_repo, usuario_repo)

    if usuario_autenticado.rol != RolUsuario.CLIENTE:
        raise HTTPException(status_code=400, detail="La sesión autenticada no pertenece a un cliente")
    if usuario_autenticado.estado == EstadoBasico.INACTIVO:
        raise HTTPException(status_code=403, detail="Cuenta inactiva")

    cliente = cliente_repo.db.query(Cliente).filter(Cliente.usuario_id == usuario_autenticado.id).first()
    if not cliente:
        cliente = Cliente(
            usuario_id=usuario_autenticado.id,
            direccion=datos.direccion,
        )
        cliente_repo.db.add(cliente)
        cliente_repo.db.flush()
    elif datos.direccion and not cliente.direccion:
        cliente.direccion = datos.direccion

    return cliente

def _crear_o_validar_cliente(datos: CheckoutClienteCreate, cliente_repo: ClienteRepository, usuario_repo: UsuarioRepository) -> Cliente:
    if not datos.email or not datos.password or not datos.nombre:
        raise HTTPException(
            status_code=400,
            detail="Se requiere nombre, email y password para usuarios no autenticados",
        )
    usuario = usuario_repo.db.query(Usuario).filter(Usuario.email == datos.email).first()
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
        usuario_repo.db.add(usuario)
        usuario_repo.db.flush()

    cliente = cliente_repo.db.query(Cliente).filter(Cliente.usuario_id == usuario.id).first()
    if not cliente:
        cliente = Cliente(
            usuario_id=usuario.id,
            direccion=datos.direccion,
        )
        cliente_repo.db.add(cliente)
        cliente_repo.db.flush()
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
    fecha_inicio: datetime, fecha_fin: datetime, ocupacion_sp_repo: OcupacionServicioProductoRepository
):
    ocupacion = ocupacion_sp_repo.db.query(OcupacionServicioProducto).filter(
        OcupacionServicioProducto.servicio_producto_id == servicio_producto_id,
        OcupacionServicioProducto.fecha_hora_inicio    == fecha_inicio,
        OcupacionServicioProducto.fecha_hora_fin       == fecha_fin,
    ).first()

    if ocupacion:
        ocupacion.cantidad_ocupada += cantidad
    else:
        ocupacion_sp_repo.db.add(OcupacionServicioProducto(
            servicio_producto_id = servicio_producto_id,
            fecha_hora_inicio    = fecha_inicio,
            fecha_hora_fin       = fecha_fin,
            cantidad_ocupada     = cantidad,
        ))

def _actualizar_ocupacion_global(
    proveedor_id: int, cantidad: int,
    fecha_inicio: datetime, fecha_fin: datetime, ocupacion_global_repo: OcupacionGlobalProveedorRepository
):
    ocupacion = ocupacion_global_repo.db.query(OcupacionGlobalProveedor).filter(
        OcupacionGlobalProveedor.proveedor_id      == proveedor_id,
        OcupacionGlobalProveedor.fecha_hora_inicio == fecha_inicio,
        OcupacionGlobalProveedor.fecha_hora_fin    == fecha_fin,
    ).first()

    if ocupacion:
        ocupacion.total_personas_ocupadas += cantidad
    else:
        ocupacion_global_repo.db.add(OcupacionGlobalProveedor(
            proveedor_id            = proveedor_id,
            fecha_hora_inicio       = fecha_inicio,
            fecha_hora_fin          = fecha_fin,
            total_personas_ocupadas = cantidad,
        ))
