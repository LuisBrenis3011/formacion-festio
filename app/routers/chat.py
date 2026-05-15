from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest, RecomendacionRequest, RecomendacionResponse
from app.services import recomendacion_service

router = APIRouter()


@router.post("/")
async def chat(
    datos: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint principal del Asistente Virtual de Festio.
    Recibe el mensaje del cliente, lo procesa con IA y retorna
    recomendaciones de servicios según disponibilidad y presupuesto.

    TODO: Integrar con el servicio de IA (ia_service.py)
    Por ahora retorna una respuesta de placeholder.
    """
    from app.services.ia_service import procesar_mensaje

    respuesta = await procesar_mensaje(
        mensaje   = datos.mensaje,
        historial = datos.historial,
        db        = db,
    )
    return respuesta


@router.post("/recomendar", response_model=RecomendacionResponse)
def recomendar(
    datos: RecomendacionRequest,
    db: Session = Depends(get_db)
):
    """Recomienda paquetes y adicionales por proveedor usando el inventario real."""
    return recomendacion_service.recomendar_evento(datos, db)
