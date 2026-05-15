from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.pago import NotificacionOut
from app.services import notificacion_service

router = APIRouter()


@router.get("/usuario/{usuario_id}", response_model=List[NotificacionOut])
def notificaciones_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Lista todas las notificaciones de un usuario ordenadas por fecha."""
    return notificacion_service.listar_notificaciones_usuario(usuario_id, db)


@router.patch("/{notificacion_id}/leer", status_code=200)
def marcar_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user)
):
    """Marca una notificación como leída."""
    return notificacion_service.marcar_leida(notificacion_id, db)