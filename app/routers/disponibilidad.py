from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.domain.reservas.schemas import ConsultaDisponibilidadRequest, DisponibilidadResponse
from app.services import disponibilidad_service
from app.services.bloqueo_service import tiempo_restante

router = APIRouter()


@router.post("/consultar", response_model=DisponibilidadResponse)
def consultar_disponibilidad(
    datos: ConsultaDisponibilidadRequest,
    db: Session = Depends(get_db)
):
    """
    Verifica en tiempo real si todos los ítems solicitados
    tienen stock disponible para el rango horario del evento.
    Llamado por el Asistente Virtual antes de mostrar opciones al cliente.
    """
    return disponibilidad_service.consultar_disponibilidad(
        proveedor_id = datos.proveedor_id,
        fecha_inicio = datos.fecha_evento_inicio,
        fecha_fin    = datos.fecha_evento_fin,
        detalles     = datos.detalles,
        db           = db,
    )


@router.get("/bloqueo/{reserva_temp_id}")
def estado_bloqueo(reserva_temp_id: str):
    """
    Retorna los segundos restantes del bloqueo temporal en Redis.
    El frontend lo usa para mostrar el contador de 10 minutos.
    """
    segundos = tiempo_restante(reserva_temp_id)
    return {
        "reserva_temp_id"  : reserva_temp_id,
        "segundos_restantes": segundos,
        "activo"           : segundos > 0,
    }