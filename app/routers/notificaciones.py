from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.domain.pagos.schemas import NotificacionOut
from app.domain.usuarios.models import Usuario
from app.repositories.notificacion_repository import NotificacionRepository, get_notificacion_repo
from app.services import notificacion_service

router = APIRouter()


@router.get("/usuario/{usuario_id}", response_model=List[NotificacionOut])
def notificaciones_usuario(
    usuario_id: int,
    repo: NotificacionRepository = Depends(get_notificacion_repo),
    usuario: Usuario = Depends(get_current_user),
):
    """Lista todas las notificaciones de un usuario ordenadas por fecha."""
    if usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede ver las notificaciones de otro usuario",
        )

    return notificacion_service.listar_notificaciones_usuario(usuario.id, repo)


@router.patch("/{notificacion_id}/leer", status_code=200)
def marcar_leida(
    notificacion_id: int,
    repo: NotificacionRepository = Depends(get_notificacion_repo),
    usuario: Usuario = Depends(get_current_user),
):
    """Marca una notificación como leída."""
    return notificacion_service.marcar_leida(notificacion_id, usuario.id, repo)
