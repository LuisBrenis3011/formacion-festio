from typing import List

from sqlalchemy.orm import Session

from app.models.enums        import EstadoNotificacion
from app.models.notificacion import Notificacion
from app.schemas.pago        import NotificacionCreate


def listar_notificaciones_usuario(usuario_id: int, db: Session) -> List[Notificacion]:
    """Lista todas las notificaciones de un usuario ordenadas por fecha."""
    return db.query(Notificacion).filter(
        Notificacion.usuario_id == usuario_id
    ).order_by(Notificacion.fecha_envio.desc()).all()


def marcar_leida(notificacion_id: int, db: Session) -> dict:
    """Marca una notificación como leída."""
    notif = db.query(Notificacion).filter(Notificacion.id == notificacion_id).first()
    if notif:
        notif.estado = EstadoNotificacion.LEIDA
        db.commit()
    return {"mensaje": "Notificación marcada como leída"}


def enviar_notificacion(datos: NotificacionCreate, db: Session) -> Notificacion:
    """
    Registra y envía una notificación al usuario.
    En producción aquí iría la integración con Firebase (PUSH),
    SendGrid (EMAIL) o Twilio (SMS).
    """
    notificacion = Notificacion(
        usuario_id = datos.usuario_id,
        reserva_id = datos.reserva_id,
        tipo       = datos.tipo,
        mensaje    = datos.mensaje,
        canal      = datos.canal,
        estado     = EstadoNotificacion.ENVIADA,
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)

    # TODO: integrar canal real según datos.canal
    # if datos.canal == "EMAIL":   enviar_email(...)
    # if datos.canal == "PUSH":    enviar_push(...)
    # if datos.canal == "SMS":     enviar_sms(...)

    return notificacion


def notificar_confirmacion_reserva(
    usuario_cliente_id:   int,
    usuario_proveedor_id: int,
    reserva_id:           int,
    db:                   Session
):
    """
    Dispara las dos notificaciones simultáneas al confirmar una reserva:
    una al cliente y otra al proveedor.
    """
    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_cliente_id,
        reserva_id = reserva_id,
        tipo       = "CONFIRMACION",
        mensaje    = "¡Tu reserva fue confirmada! Revisa los detalles en tu perfil.",
        canal      = "PUSH",
    ), db)

    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_proveedor_id,
        reserva_id = reserva_id,
        tipo       = "CONFIRMACION",
        mensaje    = "Tienes una nueva reserva confirmada. Revisa los detalles en tu panel.",
        canal      = "PUSH",
    ), db)


def notificar_fallo_pago(usuario_id: int, reserva_id: int, db: Session):
    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_id,
        reserva_id = reserva_id,
        tipo       = "RECORDATORIO",
        mensaje    = "Tu pago no pudo procesarse. Puedes reintentar antes de que expire el tiempo.",
        canal      = "PUSH",
    ), db)


def notificar_bloqueo_expirado(usuario_id: int, db: Session):
    enviar_notificacion(NotificacionCreate(
        usuario_id = usuario_id,
        reserva_id = None,
        tipo       = "RECORDATORIO",
        mensaje    = "El tiempo para completar tu reserva expiró. El inventario fue liberado.",
        canal      = "PUSH",
    ), db)
