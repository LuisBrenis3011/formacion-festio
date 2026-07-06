from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.domain.pagos.schemas import NotificacionOut
from app.repositories.notificacion_repository import NotificacionRepository, get_notificacion_repo
from app.services import notificacion_service

router = APIRouter()


@router.get("/usuario/{usuario_id}", response_model=List[NotificacionOut])
def notificaciones_usuario(
    usuario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: NotificacionRepository = Depends(get_notificacion_repo),
    _: int = Depends(get_current_user),
):
    return notificacion_service.listar_notificaciones_usuario(usuario_id, repo, skip=skip, limit=limit)


@router.patch("/{notificacion_id}/leer", status_code=200)
def marcar_leida(
    notificacion_id: int,
    repo: NotificacionRepository = Depends(get_notificacion_repo),
    _: int = Depends(get_current_user)
):
    """Marca una notificación como leída."""
    return notificacion_service.marcar_leida(notificacion_id, repo)
