from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest
from app.services.ia_service import procesar_mensaje

router = APIRouter()

@router.post("/recomendar")
async def chat_recomendar(
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
        db=db,
    )
    return respuesta
