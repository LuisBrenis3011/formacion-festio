from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_current_proveedor
from app.domain.usuarios.models import Proveedor
from app.repositories.notificacion_repository import NotificacionRepository, get_notificacion_repo
from app.repositories.reserva_repository import ReservaRepository, get_reserva_repo
from app.services import proveedor_operaciones_service


class ReservaOperativaOut(BaseModel):
    reserva_id: int
    evento_id: int
    estado_reserva: str
    estado_operativo: str
    estado_operativo_actualizado_at: Optional[str] = None
    cliente_nombre: str
    nombre_evento: str
    fecha_evento_inicio: datetime
    direccion: str
    puede_en_camino: bool
    puede_iniciar_show: bool
    puede_finalizar: bool


router = APIRouter()


@router.get("/reservas-operativas", response_model=List[ReservaOperativaOut])
def listar_reservas_operativas(
    proveedor: Proveedor = Depends(get_current_proveedor),
    reserva_repo: ReservaRepository = Depends(get_reserva_repo),
    notificacion_repo: NotificacionRepository = Depends(get_notificacion_repo),
):
    return proveedor_operaciones_service.listar_reservas_operativas(
        proveedor,
        reserva_repo,
        notificacion_repo,
    )


@router.patch("/reservas-operativas/{reserva_id}/en-camino", response_model=ReservaOperativaOut)
def marcar_en_camino(
    reserva_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    reserva_repo: ReservaRepository = Depends(get_reserva_repo),
    notificacion_repo: NotificacionRepository = Depends(get_notificacion_repo),
):
    return proveedor_operaciones_service.avanzar_estado_operativo(
        reserva_id,
        "EN_CAMINO",
        proveedor,
        reserva_repo,
        notificacion_repo,
    )


@router.patch("/reservas-operativas/{reserva_id}/iniciar-show", response_model=ReservaOperativaOut)
def iniciar_show(
    reserva_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    reserva_repo: ReservaRepository = Depends(get_reserva_repo),
    notificacion_repo: NotificacionRepository = Depends(get_notificacion_repo),
):
    return proveedor_operaciones_service.avanzar_estado_operativo(
        reserva_id,
        "EN_PROGRESO",
        proveedor,
        reserva_repo,
        notificacion_repo,
    )


@router.patch("/reservas-operativas/{reserva_id}/finalizar", response_model=ReservaOperativaOut)
def finalizar_evento(
    reserva_id: int,
    proveedor: Proveedor = Depends(get_current_proveedor),
    reserva_repo: ReservaRepository = Depends(get_reserva_repo),
    notificacion_repo: NotificacionRepository = Depends(get_notificacion_repo),
):
    return proveedor_operaciones_service.avanzar_estado_operativo(
        reserva_id,
        "FINALIZADO",
        proveedor,
        reserva_repo,
        notificacion_repo,
    )
