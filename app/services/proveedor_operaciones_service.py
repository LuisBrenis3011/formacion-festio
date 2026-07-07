import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.domain.common.enums import CanalNotificacion, EstadoReserva, TipoNotificacion
from app.domain.notificaciones.models import Notificacion
from app.domain.pagos.schemas import NotificacionCreate
from app.domain.reservas.models import Evento, Reserva
from app.domain.usuarios.models import Cliente, Proveedor, Usuario
from app.redis_client import redis_client
from app.repositories.notificacion_repository import NotificacionRepository
from app.repositories.reserva_repository import ReservaRepository
from app.services import notificacion_service


_KEY_PREFIX = "logistica:reserva"
_AUDIT_PREFIX = "AUDIT_LOGISTICA:"
_MEMORY_ESTADOS: dict[str, dict] = {}
_TRANSICIONES = {
    "PENDIENTE": "EN_CAMINO",
    "EN_CAMINO": "EN_PROGRESO",
    "EN_PROGRESO": "FINALIZADO",
}
_MENSAJES_CLIENTE = {
    "EN_CAMINO": "Tu proveedor ya va en camino hacia tu evento.",
    "EN_PROGRESO": "Tu evento ya ha iniciado.",
    "FINALIZADO": "Tu evento ha sido marcado como finalizado.",
}


def listar_reservas_operativas(
    proveedor: Proveedor,
    reserva_repo: ReservaRepository,
    notificacion_repo: NotificacionRepository,
) -> list[dict]:
    rows = (
        reserva_repo.db.query(Reserva, Evento, Usuario)
        .join(Evento, Reserva.evento_id == Evento.id)
        .join(Cliente, Evento.cliente_id == Cliente.id)
        .join(Usuario, Cliente.usuario_id == Usuario.id)
        .filter(
            Reserva.proveedor_id == proveedor.id,
            Reserva.deleted_at == None,
            Reserva.estado != EstadoReserva.CANCELADA,
        )
        .order_by(Evento.fecha_evento_inicio.asc(), Reserva.id.asc())
        .all()
    )

    return [
        _serializar_reserva_operativa(
            reserva=reserva,
            evento=evento,
            cliente_usuario=cliente_usuario,
            proveedor=proveedor,
            notificacion_repo=notificacion_repo,
        )
        for reserva, evento, cliente_usuario in rows
    ]


def avanzar_estado_operativo(
    reserva_id: int,
    estado_destino: str,
    proveedor: Proveedor,
    reserva_repo: ReservaRepository,
    notificacion_repo: NotificacionRepository,
) -> dict:
    reserva, evento, cliente_usuario = _obtener_reserva_operativa(
        reserva_id, proveedor, reserva_repo
    )

    if reserva.estado != EstadoReserva.CONFIRMADA:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden gestionar reservas confirmadas",
        )

    estado_actual, _ = obtener_estado_operativo(
        reserva.id,
        proveedor.usuario_id,
        notificacion_repo,
    )
    estado_esperado = _TRANSICIONES.get(estado_actual)
    if not estado_esperado:
        raise HTTPException(
            status_code=400,
            detail="La reserva ya no admite más cambios operativos",
        )
    if estado_destino != estado_esperado:
        raise HTTPException(
            status_code=400,
            detail=f"La siguiente transición válida es {estado_esperado}",
        )

    updated_at = datetime.utcnow().isoformat()
    _guardar_estado_operativo(reserva.id, estado_destino, updated_at)
    _registrar_auditoria(proveedor, reserva.id, estado_destino, notificacion_repo)
    _notificar_cliente(cliente_usuario, reserva.id, estado_destino, notificacion_repo)

    return _serializar_reserva_operativa(
        reserva=reserva,
        evento=evento,
        cliente_usuario=cliente_usuario,
        proveedor=proveedor,
        notificacion_repo=notificacion_repo,
    )


def obtener_estado_operativo(
    reserva_id: int,
    proveedor_usuario_id: int,
    notificacion_repo: NotificacionRepository,
) -> tuple[str, Optional[str]]:
    payload = _leer_estado_operativo(reserva_id)
    if payload:
        estado = payload.get("estado")
        if estado in {"PENDIENTE", "EN_CAMINO", "EN_PROGRESO", "FINALIZADO"}:
            return estado, payload.get("updated_at")

    audit = _reconstruir_desde_auditoria(reserva_id, proveedor_usuario_id, notificacion_repo)
    if audit:
        _guardar_estado_operativo(reserva_id, audit["estado"], audit.get("updated_at"))
        return audit["estado"], audit.get("updated_at")

    return "PENDIENTE", None


def _serializar_reserva_operativa(
    reserva: Reserva,
    evento: Evento,
    cliente_usuario: Usuario,
    proveedor: Proveedor,
    notificacion_repo: NotificacionRepository,
) -> dict:
    estado_operativo, actualizado_at = obtener_estado_operativo(
        reserva.id,
        proveedor.usuario_id,
        notificacion_repo,
    )
    return {
        "reserva_id": reserva.id,
        "evento_id": evento.id,
        "estado_reserva": reserva.estado.value if hasattr(reserva.estado, "value") else str(reserva.estado),
        "estado_operativo": estado_operativo,
        "estado_operativo_actualizado_at": actualizado_at,
        "cliente_nombre": f"{cliente_usuario.nombre} {cliente_usuario.apellido}".strip(),
        "nombre_evento": evento.nombre_evento,
        "fecha_evento_inicio": evento.fecha_evento_inicio,
        "direccion": evento.direccion,
        "puede_en_camino": estado_operativo == "PENDIENTE",
        "puede_iniciar_show": estado_operativo == "EN_CAMINO",
        "puede_finalizar": estado_operativo == "EN_PROGRESO",
    }


def _obtener_reserva_operativa(
    reserva_id: int,
    proveedor: Proveedor,
    reserva_repo: ReservaRepository,
) -> tuple[Reserva, Evento, Usuario]:
    row = (
        reserva_repo.db.query(Reserva, Evento, Usuario)
        .join(Evento, Reserva.evento_id == Evento.id)
        .join(Cliente, Evento.cliente_id == Cliente.id)
        .join(Usuario, Cliente.usuario_id == Usuario.id)
        .filter(
            Reserva.id == reserva_id,
            Reserva.proveedor_id == proveedor.id,
            Reserva.deleted_at == None,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Reserva operativa no encontrada")
    return row


def _registrar_auditoria(
    proveedor: Proveedor,
    reserva_id: int,
    estado: str,
    notificacion_repo: NotificacionRepository,
) -> None:
    notificacion_service.enviar_notificacion(
        NotificacionCreate(
            usuario_id=proveedor.usuario_id,
            reserva_id=reserva_id,
            tipo=TipoNotificacion.RECORDATORIO,
            mensaje=f"{_AUDIT_PREFIX}{estado}",
            canal=CanalNotificacion.PUSH,
        ),
        notificacion_repo,
    )


def _notificar_cliente(
    cliente_usuario: Usuario,
    reserva_id: int,
    estado: str,
    notificacion_repo: NotificacionRepository,
) -> None:
    mensaje = _MENSAJES_CLIENTE.get(estado)
    if not mensaje:
        return

    notificacion_service.enviar_notificacion(
        NotificacionCreate(
            usuario_id=cliente_usuario.id,
            reserva_id=reserva_id,
            tipo=TipoNotificacion.RECORDATORIO,
            mensaje=mensaje,
            canal=CanalNotificacion.PUSH,
        ),
        notificacion_repo,
    )


def _reconstruir_desde_auditoria(
    reserva_id: int,
    proveedor_usuario_id: int,
    notificacion_repo: NotificacionRepository,
) -> Optional[dict]:
    audit = (
        notificacion_repo.db.query(Notificacion)
        .filter(
            Notificacion.usuario_id == proveedor_usuario_id,
            Notificacion.reserva_id == reserva_id,
            Notificacion.mensaje.like(f"{_AUDIT_PREFIX}%"),
        )
        .order_by(Notificacion.fecha_envio.desc())
        .first()
    )
    if not audit:
        return None

    estado = audit.mensaje.replace(_AUDIT_PREFIX, "", 1)
    if estado not in {"EN_CAMINO", "EN_PROGRESO", "FINALIZADO"}:
        return None
    return {
        "estado": estado,
        "updated_at": audit.fecha_envio.isoformat() if audit.fecha_envio else None,
    }


def _guardar_estado_operativo(reserva_id: int, estado: str, updated_at: Optional[str]) -> None:
    payload = {
        "estado": estado,
        "updated_at": updated_at or datetime.utcnow().isoformat(),
    }
    key = _build_key(reserva_id)
    try:
        redis_client.set(key, json.dumps(payload, default=str))
    except RedisError:
        pass
    _MEMORY_ESTADOS[key] = payload


def _leer_estado_operativo(reserva_id: int) -> Optional[dict]:
    key = _build_key(reserva_id)
    if key in _MEMORY_ESTADOS:
        return _MEMORY_ESTADOS[key]

    try:
        payload = redis_client.get(key)
        return json.loads(payload) if payload else None
    except RedisError:
        return None


def _build_key(reserva_id: int) -> str:
    return f"{_KEY_PREFIX}:{reserva_id}"
