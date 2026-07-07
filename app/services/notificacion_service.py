from typing import List

from app.domain.common.enums import EstadoNotificacion
from app.domain.notificaciones.models import Notificacion
from app.domain.pagos.schemas import NotificacionCreate
from app.repositories.notificacion_repository import NotificacionRepository


def listar_notificaciones_usuario(usuario_id: int, repo: NotificacionRepository) -> List[Notificacion]:
    """Lista todas las notificaciones de un usuario ordenadas por fecha."""
    return repo.db.query(Notificacion).filter(
        Notificacion.usuario_id == usuario_id
    ).order_by(Notificacion.fecha_envio.desc()).all()


def marcar_leida(notificacion_id: int, repo: NotificacionRepository) -> dict:
    """Marca una notificación como leída."""
    notif = repo.get(notificacion_id)
    if notif:
        notif.estado = EstadoNotificacion.LEIDA
        repo.db.commit()
    return {"mensaje": "Notificación marcada como leída"}


def enviar_notificacion(datos: NotificacionCreate, repo: NotificacionRepository) -> Notificacion:
    """
    Registra y envía una notificación al usuario.
    """
    notificacion = Notificacion(
        usuario_id = datos.usuario_id,
        reserva_id = datos.reserva_id,
        tipo       = datos.tipo,
        mensaje    = datos.mensaje,
        canal      = datos.canal,
        estado     = EstadoNotificacion.ENVIADA,
    )
    repo.db.add(notificacion)
    repo.db.commit()
    repo.db.refresh(notificacion)

    return notificacion


def notificar_confirmacion_reserva(
    usuario_cliente_id:   int,
    usuario_proveedor_id: int,
    reserva_id:           int,
    repo:                 NotificacionRepository
):
    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_cliente_id,
        reserva_id = reserva_id,
        tipo       = "CONFIRMACION",
        mensaje    = "¡Tu reserva fue confirmada! Revisa los detalles en tu perfil.",
        canal      = "PUSH",
    ), repo)

    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_proveedor_id,
        reserva_id = reserva_id,
        tipo       = "CONFIRMACION",
        mensaje    = "Tienes una nueva reserva confirmada. Revisa los detalles en tu panel.",
        canal      = "PUSH",
    ), repo)


def notificar_fallo_pago(usuario_id: int, reserva_id: int, repo: NotificacionRepository):
    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_id,
        reserva_id = reserva_id,
        tipo       = "RECORDATORIO",
        mensaje    = "Tu pago no pudo procesarse. Puedes reintentar antes de que expire el tiempo.",
        canal      = "PUSH",
    ), repo)


def notificar_bloqueo_expirado(usuario_id: int, repo: NotificacionRepository):
    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_id,
        reserva_id = None,
        tipo       = "RECORDATORIO",
        mensaje    = "El tiempo para completar tu reserva expiró. El inventario fue liberado.",
        canal      = "PUSH",
    ), repo)
