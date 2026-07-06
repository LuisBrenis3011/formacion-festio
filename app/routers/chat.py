from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.domain.chat.schemas import ChatRequest
from app.services.ia.ia_service import procesar_mensaje

from app.core.limiter import limiter

router = APIRouter()

@router.post("/recomendar")
@limiter.limit("20/minute")
async def chat_recomendar(
    request: Request,
    datos: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint principal del Asistente Virtual de Festio.
    Recibe el mensaje del cliente, extrae el contexto con Gemini (IA) 
    y retorna recomendaciones inteligentes del inventario.
    """
    # Aquí llamamos al orquestador que tiene a Gemini
    respuesta = await procesar_mensaje(
        mensaje=datos.mensaje,
        historial=datos.historial,
        estado_conversacion=datos.estado_conversacion,
        filtro_proveedor_ids=datos.filtro_proveedor_ids,
        filtro_categoria_ids=datos.filtro_categoria_ids,
        db=db,
    )
    return respuesta
